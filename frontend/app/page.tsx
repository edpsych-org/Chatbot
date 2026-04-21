// Middleware redirects "/" to "/login" for every method. This component is
// only rendered if middleware is bypassed for some reason — keep it as a
// client-safe fallback redirect.
import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/login");
}
