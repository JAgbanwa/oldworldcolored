import { Github, Palette, Sun, Moon } from "lucide-react";
import { useTheme } from "../ThemeContext";

export default function Header() {
  const { dark, toggle } = useTheme();
  return (
    <header className="relative z-10 border-b border-zinc-800/60 dark:border-zinc-800/60 dark:bg-zinc-950/80 bg-stone-100/80 backdrop-blur-md transition-colors duration-300">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-sepia-500 to-gold-600 shadow-lg">
            <Palette className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold leading-tight dark:text-white text-zinc-900">
              OldWorld<span className="text-gold-400">Colored</span>
            </h1>
            <p className="text-[10px] font-medium uppercase tracking-widest text-zinc-500 dark:text-zinc-500">
              AI Photo &amp; Video Colorizer
            </p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex items-center gap-4">
          <a
            href="#how-it-works"
            className="hidden text-sm text-zinc-500 dark:text-zinc-400 transition hover:text-zinc-900 dark:hover:text-zinc-100 sm:block"
          >
            How it works
          </a>
          <a
            href="https://github.com/JAgbanwa/oldworldcolored"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-zinc-300 dark:border-zinc-700 px-3 py-1.5 text-sm text-zinc-600 dark:text-zinc-300 transition hover:border-zinc-500 dark:hover:border-zinc-500 hover:text-zinc-900 dark:hover:text-white"
          >
            <Github className="h-4 w-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>

          {/* Theme toggle */}
          <button
            onClick={toggle}
            aria-label="Toggle light/dark mode"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 transition hover:border-zinc-500 hover:text-zinc-900 dark:hover:text-white"
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </nav>
      </div>
    </header>
  );
}
