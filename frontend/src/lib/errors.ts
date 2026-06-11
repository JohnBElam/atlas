import axios from "axios";

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const envelopeError = error.response?.data?.error;
    if (typeof envelopeError === "string" && envelopeError.length > 0) {
      return envelopeError;
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong";
}
