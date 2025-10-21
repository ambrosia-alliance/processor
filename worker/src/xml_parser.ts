import { XMLParser } from 'fast-xml-parser';

export interface ParsedArticle {
    title: string;
    abstract: string;
    body: string;
    fullText: string;
}

export class EuropePMCXMLParser {
    private parser: XMLParser;

    constructor() {
        this.parser = new XMLParser({
            ignoreAttributes: false,
            attributeNamePrefix: '@_',
            textNodeName: '#text',
            parseTagValue: true,
            trimValues: true
        });
    }

    parse(xmlContent: string): ParsedArticle {
        try {
            const parsed = this.parser.parse(xmlContent);

            const title = this.extractTitle(parsed);
            const abstract = this.extractAbstract(parsed);
            const body = this.extractBody(parsed);

            const fullText = [title, abstract, body]
                .filter(text => text && text.length > 0)
                .join('\n\n');

            return {
                title,
                abstract,
                body,
                fullText
            };
        } catch (error) {
            throw new Error(`Failed to parse XML: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private extractTitle(parsed: any): string {
        try {
            const articleMeta = parsed?.article?.front?.['article-meta'];
            if (!articleMeta) return '';

            const titleGroup = articleMeta['title-group'];
            if (!titleGroup) return '';

            const articleTitle = titleGroup['article-title'];
            if (!articleTitle) return '';

            return this.extractText(articleTitle);
        } catch {
            return '';
        }
    }

    private extractAbstract(parsed: any): string {
        try {
            const articleMeta = parsed?.article?.front?.['article-meta'];
            if (!articleMeta) return '';

            const abstract = articleMeta.abstract;
            if (!abstract) return '';

            return this.extractText(abstract);
        } catch {
            return '';
        }
    }

    private extractBody(parsed: any): string {
        try {
            const body = parsed?.article?.body;
            if (!body) return '';

            return this.extractText(body);
        } catch {
            return '';
        }
    }

    private extractText(node: any): string {
        if (typeof node === 'string') {
            return node;
        }

        if (typeof node === 'number') {
            return String(node);
        }

        if (node === null || node === undefined) {
            return '';
        }

        if (node['#text']) {
            return String(node['#text']);
        }

        if (Array.isArray(node)) {
            return node.map(item => this.extractText(item)).join(' ');
        }

        if (typeof node === 'object') {
            const texts: string[] = [];

            for (const key of Object.keys(node)) {
                if (key.startsWith('@_')) continue;
                texts.push(this.extractText(node[key]));
            }

            return texts.filter(t => t.length > 0).join(' ');
        }

        return '';
    }
}

export function parseEuropePMCXML(xmlContent: string): ParsedArticle {
    const parser = new EuropePMCXMLParser();
    return parser.parse(xmlContent);
}

