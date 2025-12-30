import { ImageResponse } from "next/og";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export const size = {
  width: 32,
  height: 32,
};

export const contentType = "image/png";

export default function Icon() {
  const fontPath = join(
    process.cwd(),
    "src",
    "assets",
    "fonts",
    "fonnts.com-nocturneserif-semibolditalic.otf",
  );

  const fontData = readFileSync(fontPath);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0d1117",
          borderRadius: 7,
        }}
      >
        <div
          style={{
            fontFamily: "NocturneSerif",
            fontStyle: "italic",
            fontWeight: 600,
            fontSize: 18,
            lineHeight: 1,
            letterSpacing: 0.5,
            backgroundImage:
              "linear-gradient(90deg, rgb(120,244,124), rgb(54,106,156))",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            color: "transparent",
          }}
        >
          FE
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        {
          name: "NocturneSerif",
          data: fontData,
          style: "italic",
          weight: 600,
        },
      ],
    },
  );
}
