import { Link } from "react-router-dom";

function useDNT(): boolean {
  return (
    navigator.doNotTrack === "1" ||
    // @ts-expect-error — legacy IE/Edge property
    window.doNotTrack === "1" ||
    // @ts-expect-error — legacy Firefox property
    navigator.msDoNotTrack === "1"
  );
}

export default function Privacy() {
  const dntEnabled = useDNT();

  return (
    <div className="max-w-[680px] mx-auto px-6 py-10 leading-[1.7] text-[0.875rem] text-text-muted">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted no-underline mb-8 hover:text-text"
      >
        ← Back to Research Agent
      </Link>

      <h1 className="text-[1.4rem] font-semibold text-text mb-1.5">Privacy Policy</h1>
      <p className="text-sm text-text-muted mb-8">Last updated: April 2026</p>

      <h2 className="text-base font-semibold text-text mt-7 mb-2">What we collect</h2>
      <p>
        This site uses <strong>Amazon CloudFront standard access logs</strong>.
        Each request to the site generates a log entry that may include:
      </p>
      <ul className="pl-5 my-2">
        <li>IP address of the requester</li>
        <li>Date and time of the request</li>
        <li>URL path requested</li>
        <li>HTTP status code and bytes transferred</li>
        <li>User-agent string (browser/OS)</li>
      </ul>
      <p>
        We do <strong>not</strong> log cookies or query-string parameters.
        We do <strong>not</strong> use any third-party analytics or tracking
        pixels.
      </p>

      <h2 className="text-base font-semibold text-text mt-7 mb-2">How we use these logs</h2>
      <ul className="pl-5 my-2">
        <li>Aggregated traffic statistics (page popularity, geographic region)</li>
        <li>Detecting and blocking malicious or abusive requests</li>
        <li>Diagnosing technical issues</li>
      </ul>
      <p>
        Logs are stored in a private Amazon S3 bucket accessible only to the
        site operator and are <strong>automatically deleted after 120 days</strong>.
        No personal data is sold, rented, or shared with third parties.
      </p>

      <h2 className="text-base font-semibold text-text mt-7 mb-2">IP address anonymisation</h2>
      <p>
        Raw IP addresses are retained for up to <strong>7 days</strong> for
        security purposes (abuse detection). After that period they are only
        accessible in aggregated, anonymised form.
      </p>

      <h2 className="text-base font-semibold text-text mt-7 mb-2">Do Not Track</h2>
      <p>
        We respect the <strong>Do Not Track (DNT)</strong> browser signal.
        When DNT is enabled, we still receive access logs (this is a
        server-level mechanism we cannot disable per request), but we exclude
        your session from any aggregated statistical reporting.
      </p>

      <div
        className={`mt-3 p-3 rounded-[12px] text-sm ${
          dntEnabled
            ? "bg-[rgba(108,138,255,0.1)] border border-[rgba(108,138,255,0.3)] text-accent"
            : "bg-[rgba(255,255,255,0.04)] border border-border text-text-muted"
        }`}
      >
        {dntEnabled ? (
          <>
            ✓ <strong>Do Not Track is enabled</strong> in your browser. Your
            visits are excluded from statistical reporting.
          </>
        ) : (
          <>
            ℹ Do Not Track is <strong>not enabled</strong> in your browser.
            You can enable it in your browser privacy settings to opt out of
            statistical reporting.
          </>
        )}
      </div>

      <h2 className="text-base font-semibold text-text mt-7 mb-2">Contact</h2>
      <p>
        Questions about this policy? Open an issue on the project repository or
        contact me via my <a href="mailto:daniel@cryptodecision.io" className="text-accent no-underline hover:underline">email</a>.
      </p>
    </div>
  );
}
