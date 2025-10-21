import 'dotenv/config';
import axios from 'axios';
import { createSourceDatabase, Article } from './source_db.js';
import { createLocalDatabase, ClassificationRecord } from './local_db.js';
import { createProcessorClient } from './processor_client.js';
import { parseEuropePMCXML } from './xml_parser.js';

interface Config {
    sourceDbUrl: string;
    localDbUrl: string;
    pythonPath: string;
    processorScriptPath: string;
    pollIntervalMs: number;
    batchSize: number;
}

function loadConfig(): Config {
    const sourceDbUrl = process.env.SOURCE_DATABASE_URL;
    const localDbUrl = process.env.LOCAL_DATABASE_URL;
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const processorScriptPath = process.env.PROCESSOR_SCRIPT_PATH || '../classify.py';
    const pollIntervalMs = parseInt(process.env.POLL_INTERVAL_MS || '5000');
    const batchSize = parseInt(process.env.BATCH_SIZE || '10');

    if (!sourceDbUrl) {
        throw new Error('SOURCE_DATABASE_URL environment variable is required');
    }

    if (!localDbUrl) {
        throw new Error('LOCAL_DATABASE_URL environment variable is required');
    }

    return {
        sourceDbUrl,
        localDbUrl,
        pythonPath,
        processorScriptPath,
        pollIntervalMs,
        batchSize
    };
}

class ArticleProcessorWorker {
    private config: Config;
    private sourceDb: ReturnType<typeof createSourceDatabase>;
    private localDb: ReturnType<typeof createLocalDatabase>;
    private processorClient: ReturnType<typeof createProcessorClient>;
    private running: boolean = false;

    constructor(config: Config) {
        this.config = config;
        this.sourceDb = createSourceDatabase(config.sourceDbUrl);
        this.localDb = createLocalDatabase(config.localDbUrl);
        this.processorClient = createProcessorClient(config.pythonPath, config.processorScriptPath);
    }

    async start(): Promise<void> {
        console.log('Starting Article Processor Worker...');
        console.log(`Python Path: ${this.config.pythonPath}`);
        console.log(`Processor Script: ${this.config.processorScriptPath}`);
        console.log(`Poll Interval: ${this.config.pollIntervalMs}ms`);
        console.log(`Batch Size: ${this.config.batchSize}`);

        await this.sourceDb.connect();
        await this.localDb.connect();

        const isHealthy = await this.processorClient.isHealthy();
        if (!isHealthy) {
            throw new Error('Processor script is not healthy. Check Python path and dependencies.');
        }

        const health = await this.processorClient.health();
        console.log(`Processor Status: ${health.status}`);
        console.log(`Model: ${health.model}`);
        console.log(`Using Finetuned: ${health.using_finetuned}`);
        console.log(`Confidence Threshold: ${health.confidence_threshold}`);
        console.log(`Device: ${health.device}`);

        this.running = true;
        await this.pollLoop();
    }

    async stop(): Promise<void> {
        console.log('Stopping worker...');
        this.running = false;
        await this.sourceDb.close();
        await this.localDb.close();
        console.log('Worker stopped');
    }

    private async pollLoop(): Promise<void> {
        while (this.running) {
            try {
                await this.processBatch();
            } catch (error) {
                console.error('Error in poll loop:', error instanceof Error ? error.message : error);
            }

            await this.sleep(this.config.pollIntervalMs);
        }
    }

    private async processBatch(): Promise<void> {
        const articles = await this.sourceDb.getUnprocessedArticles(this.config.batchSize);

        if (articles.length === 0) {
            return;
        }

        console.log(`\nProcessing ${articles.length} articles...`);

        for (const article of articles) {
            await this.processArticle(article);
        }

        const stats = await this.localDb.getClassificationStats();
        console.log(`\nTotal articles processed: ${stats.total_articles}`);
        console.log(`Total classifications: ${stats.total_classifications}`);
    }

    private async processArticle(article: Article): Promise<void> {
        const logId = await this.localDb.logProcessingStart(article.id);

        try {
            console.log(`\nProcessing article: ${article.id}`);
            console.log(`Title: ${article.title}`);

            if (!article.contenturl) {
                throw new Error('Article has no content URL');
            }

            const xmlContent = await this.fetchXML(article.contenturl);
            const parsedArticle = parseEuropePMCXML(xmlContent);

            console.log(`Extracted text length: ${parsedArticle.fullText.length} characters`);

            const result = await this.processorClient.classify(parsedArticle.fullText);

            console.log(`Sentences: ${result.sentence_count}`);
            console.log(`Classifications: ${result.classifications.length}`);

            if (result.classifications.length > 0) {
                const classifications: ClassificationRecord[] = result.classifications.map(c => ({
                    article_id: article.id,
                    article_title: article.title,
                    therapy_id: article.therapyid,
                    sentence_text: c.sentence,
                    sentence_idx: c.sentence_idx,
                    category: c.category,
                    confidence: c.confidence
                }));

                await this.localDb.insertClassifications(classifications);
                console.log(`Stored ${classifications.length} classifications`);
            }

            await this.localDb.logProcessingComplete(
                logId,
                result.sentence_count,
                result.classifications.length
            );

            await this.sourceDb.markArticleProcessed(article.id);
            console.log(`Marked article as processed`);

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            console.error(`Failed to process article ${article.id}:`, errorMessage);
            await this.localDb.logProcessingFailed(logId, errorMessage);
        }
    }

    private async fetchXML(url: string): Promise<string> {
        try {
            const response = await axios.get(url, {
                timeout: 30000,
                responseType: 'text'
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to fetch XML from ${url}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

async function main() {
    const config = loadConfig();
    const worker = new ArticleProcessorWorker(config);

    process.on('SIGINT', async () => {
        console.log('\nReceived SIGINT, shutting down gracefully...');
        await worker.stop();
        process.exit(0);
    });

    process.on('SIGTERM', async () => {
        console.log('\nReceived SIGTERM, shutting down gracefully...');
        await worker.stop();
        process.exit(0);
    });

    try {
        await worker.start();
    } catch (error) {
        console.error('Fatal error:', error instanceof Error ? error.message : error);
        process.exit(1);
    }
}

main();

