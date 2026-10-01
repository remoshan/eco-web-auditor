export interface paths {
    "/api/audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["audit_api_audit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/compare": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["compare_api_compare_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/methodology": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["methodology_api_methodology_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        AssetInfo: {
            name: string;
            url: string;
            asset_type: "image" | "script" | "css" | "font" | "media";
            size_bytes: number;
            co2_grams: number;
            saving_co2_grams: number;
            status: "green" | "amber" | "red";
            optimization_tip: string;
        };
        AuditRequest: {
            url: string;
            refresh: boolean;
        };
        AuditResponse: {
            id: string;
            url: string;
            audited_at: string;
            grade: string;
            score: number;
            total_co2: number;
            annual_co2_kg: number;
            total_bytes: number;
            request_count: number;
            categories: components["schemas"]["CategoryBreakdown"][];
            rating: string;
            trees_to_offset: number;
            page_weight_mb: number;
            comparison: string;
            assets: components["schemas"]["AssetInfo"][];
            ml_prediction: components["schemas"]["MLPrediction"];
            potential: components["schemas"]["Potential"];
            green_hosting: components["schemas"]["GreenHosting"] | null;
        };
        AuditSummary: {
            id: string;
            url: string;
            audited_at: string;
            grade: string;
            score: number;
            total_co2: number;
            annual_co2_kg: number;
            total_bytes: number;
            request_count: number;
            categories: components["schemas"]["CategoryBreakdown"][];
        };
        CategoryBreakdown: {
            name: string;
            count: number;
            total_bytes: number;
            total_co2: number;
            percentage: number;
        };
        CompareRequest: {
            a: components["schemas"]["AuditSummary"];
            b: components["schemas"]["AuditSummary"];
        };
        CompareResponse: {
            older: components["schemas"]["CompareSide"];
            newer: components["schemas"]["CompareSide"];
            verdict: "better" | "worse" | "same";
            summary: string;
            metrics: components["schemas"]["CompareRow"][];
            categories: components["schemas"]["CompareRow"][];
        };
        CompareRow: {
            key: "score" | "total_co2" | "annual_co2_kg" | "total_bytes" | "request_count" | "category";
            label: string;
            older: number;
            newer: number;
            change_pct: number | null;
            direction: "up" | "down" | "same";
            verdict: "better" | "worse" | "same";
        };
        CompareSide: {
            id: string;
            url: string;
            audited_at: string;
            grade: string;
            score: number;
            total_co2: number;
        };
        GradeBand: {
            grade: string;
            max_co2: number | null;
            score: number;
        };
        GreenHosting: {
            green: boolean;
            hosted_by: string | null;
        };
        HTTPValidationError: {
            detail?: components["schemas"]["ValidationError"][];
        };
        MLPrediction: {
            predicted_co2_grams: number;
            model_name: string;
            r2_score: number;
            difference_pct: number | null;
            agreement: ("close" | "divergent") | null;
        };
        Methodology: {
            energy_per_gb: number;
            carbon_intensity: number;
            car_grams_per_km: number;
            monthly_visits: number;
            tree_kg_per_year: number;
            grades: components["schemas"]["GradeBand"][];
            ratings: components["schemas"]["RatingBand"][];
            asset_status: {
                [key: string]: {
                    [key: string]: number;
                };
            };
            savings_rates: {
                [key: string]: {
                    [key: string]: number;
                };
            };
            ml_model: components["schemas"]["ModelInfo"];
        };
        ModelInfo: {
            model_name: string;
            r2_score: number;
            mae: number;
            rmse: number;
            n_samples: number;
            n_features: number;
            agreement_tolerance_pct: number;
        };
        Potential: {
            total_co2: number;
            grade: string;
            score: number;
            saving_pct: number;
        };
        RatingBand: {
            min_score: number;
            label: string;
        };
        ValidationError: {
            loc: (string | number)[];
            msg: string;
            type: string;
            input?: unknown;
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    audit_api_audit_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AuditRequest"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditResponse"];
                };
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    compare_api_compare_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CompareRequest"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompareResponse"];
                };
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    methodology_api_methodology_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Methodology"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
