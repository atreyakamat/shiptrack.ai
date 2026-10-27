import { PackageSearch } from "lucide-react";
import Link from "next/link";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 font-display text-lg font-bold">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-sky to-indigo text-ink">
        <PackageSearch size={18} aria-hidden />
      </span>
      ShipTrack <span className="text-sky">AI</span>
    </Link>
  );
}
