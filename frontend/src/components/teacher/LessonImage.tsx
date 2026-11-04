"use client";

import { useState } from "react";
import Image from "next/image";

export function LessonImage({ source, fallback, alt, sizes }: { source?: string; fallback: string; alt: string; sizes: string }) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const src = source && source !== failedSource ? source : fallback;
  return <Image unoptimized src={src} fill sizes={sizes} alt={alt} onError={() => setFailedSource(source ?? fallback)} />;
}
