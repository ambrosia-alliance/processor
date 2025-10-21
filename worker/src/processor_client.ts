import { spawn } from 'child_process';
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
    private mode: 'subprocess' | 'http';
    private command?: string;
    private args?: string[];
    private httpClient?: AxiosInstance;

    constructor(pythonPath: string = 'python', scriptPath: string = '../classify.py') {
        if (pythonPath.startsWith('http://') || pythonPath.startsWith('https://')) {
            this.mode = 'http';
            this.httpClient = axios.create({
                baseURL: pythonPath,
                timeout: 300000,
                headers: { 'Content-Type': 'application/json' }
            });
        } else if (pythonPath.startsWith('ssh ')) {
            this.mode = 'subprocess';
            const parts = pythonPath.split(' ');
            this.command = parts[0];
            this.args = [...parts.slice(1), scriptPath];
        } else {
            this.mode = 'subprocess';
            this.command = pythonPath;
            this.args = [scriptPath];
        }
    }

    async health(): Promise<ProcessorHealth> {
        if (this.mode === 'http') {
            return this.healthHttp();
        } else {
            return this.healthSubprocess();
        }
    }

    async classify(text: string): Promise<ClassificationResponse> {
        if (this.mode === 'http') {
            return this.classifyHttp(text);
        } else {
            return this.classifySubprocess(text);
        }
    }

    private async healthHttp(): Promise<ProcessorHealth> {
        try {
            const response = await this.httpClient!.get<ProcessorHealth>('/health');
            return response.data;
        } catch (error) {
            throw new Error(`HTTP health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private async classifyHttp(text: string): Promise<ClassificationResponse> {
        try {
            const response = await this.httpClient!.post<ClassificationResponse>('/classify', { text });
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const message = error.response?.data?.error || error.message;
                throw new Error(`HTTP classification failed: ${message}`);
            }
            throw new Error(`HTTP classification failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private async healthSubprocess(): Promise<ProcessorHealth> {
        return new Promise((resolve, reject) => {
            const healthArgs = [...this.args!, '--health'];
            const process = spawn(this.command!, healthArgs);

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Health check failed: ${stderr}`));
                    return;
                }

                try {
                    const health = JSON.parse(stdout);
                    resolve(health);
                } catch (error) {
                    reject(new Error(`Failed to parse health response: ${error instanceof Error ? error.message : 'Unknown error'}`));
                }
            });

            process.on('error', (error) => {
                reject(new Error(`Failed to spawn process: ${error.message}`));
            });
        });
    }

    private async classifySubprocess(text: string): Promise<ClassificationResponse> {
        return new Promise((resolve, reject) => {
            const process = spawn(this.command!, this.args!);

            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.stdin.write(text);
            process.stdin.end();

            process.on('close', (code) => {
                if (code !== 0) {
                    try {
                        const errorData = JSON.parse(stderr);
                        reject(new Error(`Classification failed: ${errorData.error}`));
                    } catch {
                        reject(new Error(`Classification failed: ${stderr}`));
                    }
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (error) {
                    reject(new Error(`Failed to parse classification response: ${error instanceof Error ? error.message : 'Unknown error'}`));
                }
            });

            process.on('error', (error) => {
                reject(new Error(`Failed to spawn process: ${error.message}`));
            });
        });
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

export function createProcessorClient(pythonPath?: string, scriptPath?: string): ProcessorClient {
    return new ProcessorClient(pythonPath, scriptPath);
}
