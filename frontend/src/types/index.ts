export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'researcher' | 'student';
  institution?: string;
  bio?: string;
  research_interests?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export type IngestionStatus = 'pending' | 'parsing' | 'chunking' | 'extracting' | 'indexing' | 'completed' | 'failed';

export interface Document {
  id: number;
  title: string;
  filename: string;
  file_size: number;
  mime_type: string;
  status: IngestionStatus;
  error_message?: string;
  authors?: string[];
  abstract?: string;
  keywords?: string[];
  publication_date?: string;
  references?: string[];
  uploaded_by: number;
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string; // Paper, Concept, Author, Organization, Technology
  properties: Record<string, any>;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string; // RELATED_TO, USES, DEPENDS_ON, CAUSES, IMPROVES, etc.
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
  citations?: Array<{
    citation_key: string;
    document_title: string;
    text_snippet: string;
  }>;
  confidenceScore?: number;
  graphPaths?: any[];
}
