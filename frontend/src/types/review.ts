export type IssueSeverity = 'Critical' | 'High' | 'Medium' | 'Low';

export type IssueType = 'Bugs' | 'Smells' | 'Security' | 'SOLID' | 'Complexity' | 'Optimization' | 'Maintainability' | 'Best Practices' | 'Naming';

export interface Issue {
  issue_id?: string;
  severity: IssueSeverity;
  line_number: number;
  description: string;
  rule_type: string;
  ai_explanation?: string;
  file?: string;
  suggestion?: string;
  source?: 'Static' | 'AI' | 'Static + AI';
  confidence?: number;
}

export interface LanguageDetectionResult {
  selected_language: string;
  detected_language: string;
  confidence: number;
  is_match: boolean;
  evidence: string[];
  final_language?: string;
  language_switched?: boolean;
}

export interface ReviewMetadata {
  quality_score?: number;
  maintainability_grade?: string;
  tech_debt?: string;
  cyclomatic_complexity?: number;
  est_refactoring_time?: string;
  security_score?: number;
  performance_score?: number;
  ai_summary?: string;
  issue_counts?: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  repo_insights?: {
    file_count: number;
    largest_files: Array<{name: string; size: number}>;
    language_distribution: Record<string, string>;
    repo_health_score: number;
  };
  scoring_engine?: {
    version: string;
    overall_quality: number;
    security_score: number;
    performance_score: number;
    maintainability_score: number;
    maintainability_grade: string;
    technical_debt_score: number;
  };
  language_detection?: LanguageDetectionResult;
  ai_status?: 'available' | 'unavailable';
  ai_unavailable_reason?: 'rate_limit' | 'provider_error' | string;
}

export interface Review {
  id: string;
  user_id: string;
  language_id: string;
  language?: { id: string; name: string };
  title: string;
  source_code: string;
  improved_code?: string;
  issues: Issue[];
  quality_score?: number;
  metadata: ReviewMetadata;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_name?: string;
  file_size?: number;
  repo_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewCreatePayload {
  title: string;
  language_id?: string;
  source_code?: string;
  repo_url?: string;
}

export interface ReviewFilter {
  status?: string;
  language?: string;
  skip?: number;
  limit?: number;
  maxScore?: number;
}

export interface ReviewSummary {
  id: string;
  repositoryUrl: string;
  branch: string;
  status: string;
  overallScore: number;
  issuesFound: number;
  criticalIssues: number;
  createdAt: string;
}

