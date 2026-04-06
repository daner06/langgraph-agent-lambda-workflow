import { Link } from "react-router-dom";
import "../App.css";

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
    <div className="privacy-page">
      <Link to="/" className="privacy-back">
        ← Back to Research Agent
      </Link>

      <h1>Privacy Policy</h1>
      <p className="privacy-updated">Last updated: April 2025</p>

      <h2>What we collect</h2>
      <p>
        This site uses <strong>Amazon CloudFront standard access logs</strong>.
        Each request to the site generates a log entry that may include:
      </p>
      <ul>
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

      <h2>How we use these logs</h2>
      <ul>
        <li>Aggregated traffic statistics (page popularity, geographic region)</li>
        <li>Detecting and blocking malicious or abusive requests</li>
        <li>Diagnosing technical issues</li>
      </ul>
      <p>
        Logs are stored in a private Amazon S3 bucket accessible only to the
        site operator and are <strong>automatically deleted after 120 days</strong>.
        No personal data is sold, rented, or shared with third parties.
      </p>

      <h2>IP address anonymisation</h2>
      <p>
        Raw IP addresses are retained for up to <strong>7 days</strong> for
        security purposes (abuse detection). After that period they are only
        accessible in aggregated, anonymised form.
      </p>

      <h2>Do Not Track</h2>
      <p>
        We respect the <strong>Do Not Track (DNT)</strong> browser signal.
        When DNT is enabled, we still receive access logs (this is a
        server-level mechanism we cannot disable per request), but we exclude
        your session from any aggregated statistical reporting.
      </p>

      <div
        className={`dnt-banner ${
          dntEnabled ? "dnt-banner--active" : "dnt-banner--inactive"
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

      <h2>Contact</h2>
      <p>
        Questions about this policy? Open an issue on the project repository or
        contact me via my <a href="mailto:daniel@cryptodecision.io">email</a>.
      </p>
    </div>
  );
}
