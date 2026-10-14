/**
 * API Service
 * Komunikasi dengan backend Sampling & Spec R&D
 */

// Use relative path for dev (works with Vite proxy), fallback to full URL for production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/sampling-spec-rnd';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

class SamplingSpecAPI {
  private baseUrl = API_BASE_URL;

  // ==================== TIME STUDY ENDPOINTS ====================

  async createStudy(params: {
    tenant_id: string;
    process_id: string;
    process_name: string;
    operator_id: string;
    target_sample_size?: number;
  }): Promise<ApiResponse<{ study_id: string; status: string }>> {
    try {
      const queryString = new URLSearchParams(params as any).toString();
      const response = await fetch(`${this.baseUrl}/studies/create?${queryString}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to create study: ${error}` 
      };
    }
  }

  async startStudy(studyId: string): Promise<ApiResponse<null>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/start`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to start study: ${error}` 
      };
    }
  }

  async addSample(params: {
    study_id: string;
    cycle_time_ms: number;
    element_name: string;
    is_abnormal?: boolean;
    notes?: string;
  }): Promise<ApiResponse<null>> {
    try {
      const { study_id, ...queryParams } = params;
      const queryString = new URLSearchParams(queryParams as any).toString();
      const response = await fetch(
        `${this.baseUrl}/studies/${study_id}/add-sample?${queryString}`,
        { method: 'POST' }
      );
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to add sample: ${error}` 
      };
    }
  }

  async completeStudy(studyId: string): Promise<ApiResponse<null>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/complete`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to complete study: ${error}` 
      };
    }
  }

  async pauseStudy(studyId: string): Promise<ApiResponse<null>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/pause`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to pause study: ${error}` 
      };
    }
  }

  async resumeStudy(studyId: string): Promise<ApiResponse<null>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/resume`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to resume study: ${error}` 
      };
    }
  }

  async getStudyStats(studyId: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/stats`);
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to get stats: ${error}` 
      };
    }
  }

  async getStudyData(studyId: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/studies/${studyId}/data`);
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to get study data: ${error}` 
      };
    }
  }

  // ==================== SPECIFICATION ENDPOINTS ====================

  async createSpec(params: {
    tenant_id: string;
    spec_id: string;
    spec_name: string;
    created_by: string;
    version_number?: string;
  }): Promise<ApiResponse<{ version_id: string; status: string }>> {
    try {
      const queryString = new URLSearchParams(params as any).toString();
      const response = await fetch(`${this.baseUrl}/specs/create?${queryString}`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to create spec: ${error}` 
      };
    }
  }

  async recordSpecChange(params: {
    version_id: string;
    change_type: string;
    parameter_name: string;
    old_value: any;
    new_value: any;
    changed_by: string;
    reason?: string;
  }): Promise<ApiResponse<null>> {
    try {
      const { version_id, ...queryParams } = params;
      const queryString = new URLSearchParams(queryParams as any).toString();
      const response = await fetch(
        `${this.baseUrl}/specs/${version_id}/record-change?${queryString}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            old_value: params.old_value,
            new_value: params.new_value,
          }),
        }
      );
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to record change: ${error}` 
      };
    }
  }

  async recordDrift(params: {
    version_id: string;
    parameter_name: string;
    specification_limit: number;
    measured_value: number;
    severity?: string;
  }): Promise<ApiResponse<null>> {
    try {
      const { version_id, ...queryParams } = params;
      const queryString = new URLSearchParams(queryParams as any).toString();
      const response = await fetch(
        `${this.baseUrl}/specs/${version_id}/record-drift?${queryString}`,
        { method: 'POST' }
      );
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to record drift: ${error}` 
      };
    }
  }

  async getDriftReport(versionId: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/specs/${versionId}/drift-report`);
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to get drift report: ${error}` 
      };
    }
  }

  async getSpecData(versionId: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/specs/${versionId}/data`);
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to get spec data: ${error}` 
      };
    }
  }

  // ==================== WORKFLOW ENDPOINTS ====================

  async getWorkflowSummary(tenantId: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(
        `${this.baseUrl}/workflow/summary?tenant_id=${tenantId}`
      );
      return await response.json();
    } catch (error) {
      return { 
        success: false, 
        error: `Failed to get workflow summary: ${error}` 
      };
    }
  }

  async checkHealth(): Promise<ApiResponse<any>> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      const response = await fetch(`${this.baseUrl}/health`, {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        return { 
          success: false, 
          error: `Health check failed: ${response.status}` 
        };
      }
      
      const data = await response.json();
      return { 
        success: true,
        data: data
      };
    } catch (error) {
      return { 
        success: false, 
        error: `Backend not available: ${error}` 
      };
    }
  }
}

export const api = new SamplingSpecAPI();
export default api;
