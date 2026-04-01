import { Github, Heart } from "lucide-react";

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-zinc-800/60 bg-zinc-950/80 py-10 text-center">
      <div className="mx-auto max-w-6xl px-6">
        {/* How it works */}
        <div id="how-it-works" className="mb-10">
          <h2 className="mb-6 font-display text-2xl font-semibold text-zinc-100">
            How it works
          </h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            {[
              {
                step: "01",
                title: "Upload",
                body: "Drop any black-and-white JPG, PNG, or MP4. The app accepts photos and videos up to 500 MB.",
              },
              {
                step: "02",
                title: "AI Colorizes",
                body: "Zhang et al.'s deep CNN predicts plausible colors in the CIE LAB color space — no manual input needed.",
              },
              {
                step: "03",
                title: "Compare & Save",
                body: "Drag the slider to inspect every detail, then download your vibrant, full-color result.",
              },
            ].map(({ step, title, body }) => (
              <div
                key={step}
                className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 text-left"
              >
                <span className="font-mono text-3xl font-bold text-zinc-700">
                  {step}
                </span>
                <h3 className="mt-2 font-semibold text-zinc-100">{title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-zinc-500">{body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Credits */}
        <p className="text-sm text-zinc-600">
          Powered by{" "}
          <a
            href="https://richzhang.github.io/colorization/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 underline underline-offset-2 hover:text-zinc-300 transition"
          >
            Zhang et al. (ECCV 2016)
          </a>{" "}
          · Built with{" "}
          <Heart className="inline h-3.5 w-3.5 text-red-500" /> by{" "}
          <a
            href="https://github.com/JAgbanwa"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 underline underline-offset-2 hover:text-zinc-300 transition"
          >
            JAgbanwa
          </a>
          {" "}·{" "}
          <a
            href="https://github.com/JAgbanwa/oldworldcolored"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-zinc-500 underline underline-offset-2 hover:text-zinc-300 transition"
          >
            <Github className="h-3.5 w-3.5" /> Source
          </a>
        </p>
      </div>
    </footer>
  );
}
