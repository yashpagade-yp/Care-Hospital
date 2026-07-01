type StatusBannerProps = {
  tone?: "info" | "success" | "warning" | "error";
  children: string;
};

export function StatusBanner({ tone = "info", children }: StatusBannerProps) {
  return <div className={`status-banner status-banner--${tone}`}>{children}</div>;
}
