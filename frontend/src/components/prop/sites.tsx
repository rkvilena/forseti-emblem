import type { JSX, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

export interface SiteLink {
  label: string;
  href: string;
  Icon: (props: IconProps) => JSX.Element;
}

export function GithubIcon(props: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 2C6.48 2 2 6.48 2 12C2 16.42 4.87 20.17 8.84 21.5C9.34 21.59 9.52 21.3 9.52 21.05C9.52 20.82 9.51 20.12 9.51 19.25C7 19.8 6.35 18.4 6.35 18.4C5.9 17.36 5.24 17.08 5.24 17.08C4.31 16.5 5.31 16.52 5.31 16.52C6.34 16.6 6.88 17.59 6.88 17.59C7.79 19.13 9.27 18.69 9.86 18.45C9.95 17.8 10.21 17.35 10.5 17.11C8.44 16.87 6.27 16.05 6.27 12.73C6.27 11.76 6.61 10.98 7.17 10.39C7.08 10.15 6.77 9.24 7.24 7.99C7.24 7.99 7.97 7.74 9.5 8.82C10.19 8.63 10.93 8.54 11.67 8.54C12.41 8.54 13.15 8.63 13.84 8.82C15.37 7.74 16.1 7.99 16.1 7.99C16.57 9.24 16.26 10.15 16.17 10.39C16.73 10.98 17.07 11.76 17.07 12.73C17.07 16.06 14.89 16.86 12.82 17.1C13.18 17.4 13.49 17.99 13.49 18.92C13.49 20.25 13.48 21.33 13.48 21.63C13.48 21.88 13.66 22.18 14.17 22.08C18.13 20.17 21 16.42 21 12C21 6.48 16.52 2 12 2Z" />
    </svg>
  );
}

export function WebsiteIcon(props: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12H21" />
      <path d="M12 3C14.5 6 15.75 8.99 15.75 12C15.75 15.01 14.5 18 12 21C9.5 18 8.25 15.01 8.25 12C8.25 8.99 9.5 6 12 3Z" />
    </svg>
  );
}

export const SITES: SiteLink[] = [
  {
    label: "GitHub",
    href: "https://github.com/forsetiemblem",
    Icon: GithubIcon,
  },
  {
    label: "Website",
    href: "https://rkvilena.com",
    Icon: WebsiteIcon,
  },
];
