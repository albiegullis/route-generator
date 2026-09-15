"use client";

import dynamic from "next/dynamic";

// Since Map.tsx is right next to page.tsx, we just use "./Map"
const Map = dynamic(() => import("./Map"), { 
  ssr: false 
});

export default function Home() {
  return (
    <main className="h-screen w-full">
      <Map />
    </main>
  );
}