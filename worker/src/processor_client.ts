import axios, { AxiosInstance } from 'axios';

export interface Classification {
    sentence: string;
    sentence_idx: number;
    category: string;
    confidence: number;
}

export interface ClassificationResponse {
    classifications: Classification[];
    sentence_count: number;
}

export interface ProcessorHealth {
    status: string;
    model: string;
    confidence_threshold: number;
    using_finetuned: boolean;
    device: string;
}

export class ProcessorClient {
    private client: AxiosInstance;
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: 300000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async health(): Promise<ProcessorHealth> {
        try {
            const response = await this.client.get<ProcessorHealth>('/health');
            return response.data;
        } catch (error) {
            throw new Error(`Processor health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async classify(text: string): Promise<ClassificationResponse> {
        try {
            const response = await this.client.post<ClassificationResponse>('/classify', {
                text
            });
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const message = error.response?.data?.error || error.message;
                throw new Error(`Classification failed: ${message}`);
            }
            throw new Error(`Classification failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async isHealthy(): Promise<boolean> {
        try {
            const health = await this.health();
            return health.status === 'healthy';
        } catch {
            return false;
        }
    }
}

export function createProcessorClient(baseUrl: string): ProcessorClient {
    return new ProcessorClient(baseUrl);
}

