"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Briefcase, User, Github, ListTodo, FileText, PenLine, FilePlus2 } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/cv-editor", label: "CV Editor", icon: PenLine },
  { href: "/custom-cv", label: "Custom CV", icon: FilePlus2 },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/github", label: "GitHub", icon: Github },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 h-screen flex flex-col border-r bg-card">
      <div className="flex items-center gap-2 px-5 py-5 border-b">
        <FileText className="w-5 h-5 text-primary" />
        <span className="font-semibold text-sm tracking-tight">CV Generator</span>
      </div>
      <nav className="flex flex-col gap-1 p-3 flex-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
