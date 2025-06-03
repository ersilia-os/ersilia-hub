import { HttpErrorResponse } from "@angular/common/http";

export function mapHttpError(error: HttpErrorResponse): string {
    if (error.status === 0) {
        // client-side error
        return error.error;
    }

    const errorDetail = error != null && error.error != null && typeof error.error === 'object' && error.error['detail'];

    return errorDetail == null ? error.message : errorDetail;
}