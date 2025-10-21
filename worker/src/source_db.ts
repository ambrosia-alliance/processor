import pg from 'pg';
const { Pool } = pg;

export interface Article {
    id: string;
    title: string;
    contenturl: string | null;
    therapyid: number;
    publisheddate: Date | null;
}

export class SourceDatabase {
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
            console.log('Connected to source database');
        } catch (error) {
            throw new Error(`Failed to connect to source database: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async getUnprocessedArticles(limit: number = 10): Promise<Article[]> {
        const query = `
            SELECT id, title, contenturl, therapyid, publisheddate
            FROM article
            WHERE processed = false
            AND contenturl IS NOT NULL
            ORDER BY createdat ASC
            LIMIT $1
        `;

        try {
            const result = await this.pool.query(query, [limit]);
            return result.rows;
        } catch (error) {
            throw new Error(`Failed to fetch unprocessed articles: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async markArticleProcessed(articleId: string): Promise<void> {
        const query = `
            UPDATE article
            SET processed = true
            WHERE id = $1
        `;

        try {
            await this.pool.query(query, [articleId]);
        } catch (error) {
            throw new Error(`Failed to mark article as processed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async close(): Promise<void> {
        await this.pool.end();
    }
}

export function createSourceDatabase(connectionString: string): SourceDatabase {
    return new SourceDatabase(connectionString);
}

