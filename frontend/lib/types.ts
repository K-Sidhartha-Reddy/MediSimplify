export type User = {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Report = {
  id: string;
  user_id: string;
  file_name: string;
  extracted_text: string;
  simplified_text: string;
  important_terms: string[];
  created_at: string;
};

export type UploadResponse = {
  saved: boolean;
  report: Report | null;
  file_name: string;
  extracted_text: string;
  simplified_text: string;
  important_terms: string[];
  created_at: string;
};
