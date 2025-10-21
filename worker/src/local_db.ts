import pg from 'pg';
const { Pool } = pg;

export interface ClassificationRecord {
    article_id: string;
    article_title: string;
    therapy_id: number;
    sentence_text: string;
    sentence_idx: number;
    category: string;
    confidence: number;
    model_version?: string;
}

export interface ProcessingLogRecord {
    article_id: string;
    status: 'started' | 'completed' | 'failed';
    error_message?: string;
    sentences_processed?: number;
    classifications_count?: number;
}

export class LocalDatabase {
    private pool: pg.Pool;

    constructor(connectionString: string) {
        this.pool = new Pool({
            connectionString,
            max: 10,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 5000
        });
    }

    async connect(): Promise<void> {
        try {
            await this.pool.query('SELECT 1');
            console.log('Connected to local database');
        } catch (error) {
            throw new Error(`Failed to connect to local database: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async insertClassifications(classifications: ClassificationRecord[]): Promise<void> {
        if (classifications.length === 0) return;

        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            const query = `
                INSERT INTO article_classifications
                (article_id, article_title, therapy_id, sentence_text, sentence_idx, category, confidence, model_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            `;

            for (const classification of classifications) {
                await client.query(query, [
                    classification.article_id,
                    classification.article_title,
                    classification.therapy_id,
                    classification.sentence_text,
                    classification.sentence_idx,
                    classification.category,
                    classification.confidence,
                    classification.model_version || null
                ]);
            }

            await client.query('COMMIT');
        } catch (error) {
            await client.query('ROLLBACK');
            throw new Error(`Failed to insert classifications: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            client.release();
        }
    }

    async logProcessingStart(articleId: string): Promise<number> {
        const query = `
            INSERT INTO processing_log (article_id, status)
            VALUES ($1, 'started')
            RETURNING id
        `;

        try {
            const result = await this.pool.query(query, [articleId]);
            return result.rows[0].id;
        } catch (error) {
            throw new Error(`Failed to log processing start: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async logProcessingComplete(
        logId: number,
        sentencesProcessed: number,
        classificationsCount: number
    ): Promise<void> {
        const query = `
            UPDATE processing_log
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                sentences_processed = $2,
                classifications_count = $3
            WHERE id = $1
        `;

        try {
            await this.pool.query(query, [logId, sentencesProcessed, classificationsCount]);
        } catch (error) {
            throw new Error(`Failed to log processing complete: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async logProcessingFailed(logId: number, errorMessage: string): Promise<void> {
        const query = `
            UPDATE processing_log
            SET status = 'failed',
                completed_at = CURRENT_TIMESTAMP,
                error_message = $2
            WHERE id = $1
        `;

        try {
            await this.pool.query(query, [logId, errorMessage]);
        } catch (error) {
            throw new Error(`Failed to log processing failure: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async getClassificationStats(): Promise<{
        total_articles: number;
        total_classifications: number;
        categories: Record<string, number>;
    }> {
        const totalArticlesQuery = 'SELECT COUNT(DISTINCT article_id) as count FROM article_classifications';
        const totalClassificationsQuery = 'SELECT COUNT(*) as count FROM article_classifications';
        const categoriesQuery = 'SELECT category, COUNT(*) as count FROM article_classifications GROUP BY category';

        try {
            const [articlesResult, classificationsResult, categoriesResult] = await Promise.all([
                this.pool.query(totalArticlesQuery),
                this.pool.query(totalClassificationsQuery),
                this.pool.query(categoriesQuery)
            ]);

            const categories: Record<string, number> = {};
            for (const row of categoriesResult.rows) {
                categories[row.category] = parseInt(row.count);
            }

            return {
                total_articles: parseInt(articlesResult.rows[0].count),
                total_classifications: parseInt(classificationsResult.rows[0].count),
                categories
            };
        } catch (error) {
            throw new Error(`Failed to get classification stats: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async close(): Promise<void> {
        await this.pool.end();
    }
}

export function createLocalDatabase(connectionString: string): LocalDatabase {
    return new LocalDatabase(connectionString);
}

