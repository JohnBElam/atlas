export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="border border-red-600 bg-red-950/30 px-4 py-3 text-sm text-red-300">
      {message}
    </div>
  );
}
