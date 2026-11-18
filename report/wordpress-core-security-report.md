# Comparative Security Assessment of WordPress 4.0.38 (Site A) and WordPress 7.1.4 (Site B) on XAMPP

**Prepared by:** Olowoyobabajide
**Date:** 15 November 2026
**Environment:** Kali GNU/Linux Rolling 2026.2, XAMPP for Linux 8.2.12-0
**Test targets:** Site A (WordPress 4.0.38) and Site B (WordPress 7.1.4)
**Scanner:** WPScan 4.1.0

---

## 1. Executive summary

I built a local lab on XAMPP with two WordPress installations taken from the archives supplied in the working directory: WordPress 4.0.38 as Site A and WordPress 7.1.4 as Site B. I installed both through their native web installers, recorded the process with screenshots, and scanned each site with WPScan.

The two scans returned the same number of version-specific vulnerabilities: zero. The difference was in the status that WPScan assigned to each core. Site A was reported as **Insecure**, released on 30 November 2022, and Site B as **Latest**, released on 28 October 2026. WPScan also classed Site A's bundled Twenty Fourteen theme as out of date (1.2 against 4.5) and Site B's Twenty Twenty-Five theme as current (1.5).

The scan result did not mean the two cores carried equal risk. Site A is the final release of the 4.0 branch and has received no core fixes since 2022. The NVD record set for the version range that includes 4.0.38 contains 134 CVE entries, including 14 critical and 37 high severity. Five entries were published after 4.0.38 shipped. Three of those, CVE-2023-2745 (directory traversal, May 2023), CVE-2024-31210 (plugin-upload RCE, April 2024) and CVE-2026-87902 (template path inclusion leading to RCE, September 2026, CVSS 8.1), were not backported to the 4.0 branch. The equivalent NVD query for 7.1.4 returned no CVE entries.

The architectural comparison produced four concrete differences:

1. **Maintenance lifecycle.** Site A sits on an end-of-life branch whose last release was 4.0.38 in November 2022. Site B is on the current release line.
2. **Password storage.** Site A stores administrator passwords with phpass portable MD5 (`$P$B…`, cost 8). Site B stores them with bcrypt (`$wp$2y$10$…`, cost 10) through PHP `password_hash()`.
3. **Runtime compatibility.** WordPress 4.0.38 could not run on PHP 8.2.12 without five compatibility interventions. WordPress 7.1.4 ran without modification.
4. **Default exposure.** Both sites exposed XML-RPC, `readme.html`, externally reachable WP-Cron and verbose server headers. Site B additionally exposed the uploads directory and enumerated the `admin` user through the REST API and user sitemap.

My conclusion is that the inherent security difference between these two cores is driven less by isolated coding defects than by the presence or absence of a maintained patch pipeline, modern password cryptography, and compatibility with the current PHP runtime.

---

## 2. Scope and environment

I worked from `/home/olowoyobabajide/Documents/wordpress_work`. The two supplied archives were:

| File | Version | Size |
|---|---|---|
| `wordpress-4.0.38.zip` | 4.0.38 | 6.3 MB |
| `wordpress-7.1.4.zip` | 7.1.4 | 35.5 MB |

The host was Kali GNU/Linux Rolling 2026.2 (kernel 7.1.5), with 15 GB RAM and a graphical session on display `:0`. XAMPP for Linux 8.2.12-0 was already present at `/opt/lampp`; its stack consisted of Apache 2.4.58, MariaDB 10.4.32, PHP 8.2.12, OpenSSL 1.1.1w and ProFTPD. WPScan 4.1.0 was installed at `/usr/bin/wpscan`.

I created the working directories `src/`, `scans/`, `screenshots/`, `logs/`, `report/` and `tools/` for source archives, scan output, evidence, console captures and the report build.

---

## 3. XAMPP installation and verification

XAMPP was installed at `/opt/lampp` with the standard installer layout. I started the stack as root:

```bash
sudo /opt/lampp/lampp start
```

Apache, MySQL and ProFTPD all reported `ok`. A status check and a direct request to `http://localhost/` returned HTTP 302 to the XAMPP dashboard, confirming that the web tier was serving. I recorded the running stack and the databases in the console capture in Figure 2.

![Figure 1 – XAMPP 8.2.12 dashboard on localhost](screenshots/11-xampp-dashboard.jpg){ .tall }

*Figure 1. The XAMPP dashboard after starting Apache, MariaDB and ProFTPD. The page identifies the stack as XAMPP for Linux 8.2.12 and states that the default configuration is intended for development and is insecure if exposed to others.*

![Figure 2 – XAMPP services and databases](screenshots/14-xampp-status-and-databases.png)

*Figure 2. Console evidence of the service start, the running status of Apache/MySQL/ProFTPD, the `wp_sitea` and `wp_siteb` databases, and the table counts (11 and 12).*

I connected to MariaDB as `root` with the XAMPP default empty password and created one database per site:

```sql
CREATE DATABASE wp_sitea CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE DATABASE wp_siteb CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

phpMyAdmin confirmed both schemas under the `root@localhost` account.

![Figure 3 – Databases in phpMyAdmin](screenshots/13-phpmyadmin-databases.jpg){ .tall }

*Figure 3. phpMyAdmin 5.2.1 listing `wp_sitea` and `wp_siteb` alongside the default XAMPP schemas.*

---

## 4. WordPress deployment

### 4.1 Site A – WordPress 4.0.38

I extracted the archive and copied it to the document root:

```bash
unzip -q wordpress-4.0.38.zip -d src/siteA
sudo cp -a src/siteA/wordpress /opt/lampp/htdocs/siteA
sudo chown -R daemon:daemon /opt/lampp/htdocs/siteA
```

The reported core version was:

```php
$wp_version = '4.0.38';
```

I generated `wp-config.php` from the bundled sample, set the database to `wp_sitea` with the `root` account, and inserted a fresh set of authentication keys and salts from the WordPress secret-key API.

### 4.2 Site B – WordPress 7.1.4

I repeated the procedure for the second archive:

```bash
unzip -q wordpress-7.1.4.zip -d src/siteB
sudo cp -a src/siteB/wordpress /opt/lampp/htdocs/siteB
sudo chown -R daemon:daemon /opt/lampp/htdocs/siteB
```

The reported core version was:

```php
$wp_version = '7.1.4';
```

Site B used the database `wp_siteb` and its own salt set.

### 4.3 PHP 8.2 compatibility work on WordPress 4.0.38

WordPress 7.1.4 installed and ran on PHP 8.2.12 without changes. WordPress 4.0.38 did not. I recorded five distinct failures and applied the minimum changes needed to make the legacy core executable. None of these changes altered the reported core version.

**Failure 1 – uncaught mysqli exception.** The first request returned HTTP 500 with an empty body. The PHP log showed:

```
PHP Fatal error: Uncaught mysqli_sql_exception: Table 'wp_sitea.wp_options' doesn't exist
in /opt/lampp/htdocs/siteA/wp-includes/wp-db.php:1781
```

PHP 8.1 changed the default mysqli error mode to exceptions, which the 4.0 `wpdb` class does not catch. I added `mysqli_report(MYSQLI_REPORT_OFF);` at the top of `wp-config.php`.

**Failure 2 – removed `get_magic_quotes_gpc()`.** The next request failed in `wp_magic_quotes()`:

```
PHP Fatal error: Uncaught Error: Call to undefined function get_magic_quotes_gpc()
in /opt/lampp/htdocs/siteA/wp-includes/load.php:585
```

The function was removed in PHP 8.0. I added a compatibility definition that returns `false`.

**Failure 3 – removed `create_function()`.** The 4.0 code base calls `create_function()` in the POMO translation layer and the Atom parser. I added a compatibility implementation that returns a closure through `eval()`, preserving the call sites.

**Failure 4 – PHP 4-style constructor in phpass.** After the installer completed, the administrator hash in `wp_users` was `*` and login failed. `wp_hash_password()` returned `*` because `PasswordHash` uses a PHP 4-style constructor:

```php
function PasswordHash($iteration_count_log2, $portable_hashes)
```

PHP 8 no longer treats a method with the class name as a constructor, so the object's `itoa64` alphabet was never initialised and `gensalt_private()` produced only `$P$`. I added a `__construct()` wrapper that calls the legacy method. A direct test then produced a valid hash:

```
$P$BWQ2c3DiPYUZyRr4GAZjBf0Gtx28s70
```

**Failure 5 – scalar offset in `wp_signon()`.** The login page returned HTTP 500 with:

```
PHP Fatal error: Uncaught TypeError: Cannot access offset of type string on string
in /opt/lampp/htdocs/siteA/wp-includes/user.php:39
```

`wp-login.php` passed an empty string as the credentials array, which PHP 8 rejects when `wp_signon()` writes `$credentials['remember']`. I changed the call to `wp_signon( array(), $secure_cookie )`.

After these changes the installer, login, dashboard and front end all worked.

---

## 5. Installation results

### 5.1 Site A installer

![Figure 4 – WordPress 4.0.38 language selection](screenshots/01-siteA-install-language.jpg)

*Figure 4. The legacy installer opens with a language list and the 2014-era WordPress mark.*

![Figure 5 – WordPress 4.0.38 installation form](screenshots/02-siteA-install-form.jpg)

*Figure 5. The 4.0.38 installer form. The password fields have no visibility toggle or strength meter output beyond the legacy strength indicator.*

![Figure 6 – WordPress 4.0.38 installation success](screenshots/03-siteA-install-success.jpg)

*Figure 6. The installer confirms completion and creates the administrator account.*

### 5.2 Site B installer

![Figure 7 – WordPress 7.1.4 language selection](screenshots/05-siteB-install-language.jpg)

*Figure 7. The current installer uses the modern WordPress identity and a larger language catalogue.*

![Figure 8 – WordPress 7.1.4 installation form](screenshots/06-siteB-install-form.jpg)

*Figure 8. The 7.1.4 form generates a strong password by default, offers a visibility toggle and reports password strength inline.*

![Figure 9 – WordPress 7.1.4 installation success](screenshots/07-siteB-install-success.jpg)

*Figure 9. The modern installer completes and links directly to the login screen.*

### 5.3 Dashboards and front ends

![Figure 10 – Site A dashboard](screenshots/04-siteA-dashboard.jpg){ .tall }

*Figure 10. Site A dashboard. The At a Glance widget reports "WordPress 4.0.38 running Twenty Fourteen theme", and the red banner states that 7.1.4 is available, that 4.0.38 is no longer supported, and that security updates will not be received.*

![Figure 11 – Site B dashboard](screenshots/08-siteB-dashboard.jpg){ .tall }

*Figure 11. Site B dashboard. The At a Glance widget reports "WordPress 7.1.4 running Twenty Twenty-Five theme", with Site Health and the current-version welcome panel.*

![Figure 12 – Site A front end](screenshots/09-siteA-frontend.jpg)

*Figure 12. Site A front end with Twenty Fourteen and the administrator toolbar.*

![Figure 13 – Site B front end](screenshots/10-siteB-frontend.jpg)

*Figure 13. Site B front end with the Twenty Twenty-Five block theme.*

I verified the stored password formats directly in MariaDB. Site A held a phpass MD5 hash (`$P$B…`); Site B held a bcrypt hash (`$wp$2y$10$…`).

![Figure 14 – Version and password-hash evidence](screenshots/15-version-and-hash-evidence.png)

*Figure 14. The two version strings and the first 14 characters of each administrator hash, read from `wp_users`.*

---

## 6. WPScan methodology

I used WPScan 4.1.0 with the API token supplied for this assessment. The token value is redacted in every command and screenshot. The free plan allows 25 API requests per day; the two full scans and the preceding verification queries consumed the allowance.

Before scanning I updated the local WPScan database:

```bash
wpscan --update
```

The first update attempt failed with `Could not resolve hostname` for `data.wpscan.org`. The local resolver returned only IPv6 addresses for that host, and the resolver path in use did not complete the lookup. I added the Cloudflare IPv4 addresses for `data.wpscan.org` (`104.21.63.114` and `172.67.145.113`) to `/etc/hosts`; the update then completed.

The scan commands were:

```bash
wpscan --url http://localhost/siteA/ --api-token [REDACTED] \
       --random-user-agent --no-banner --disable-tls-checks

wpscan --url http://localhost/siteB/ --api-token [REDACTED] \
       --random-user-agent --no-banner --disable-tls-checks
```

I also ran each site with `--enumerate u` and JSON output:

```bash
wpscan --url http://localhost/siteA/ --api-token [REDACTED] --enumerate u \
       --random-user-agent --no-banner --format json --output scans/siteA.json

wpscan --url http://localhost/siteB/ --api-token [REDACTED] --enumerate u \
       --random-user-agent --no-banner --format json --output scans/siteB.json
```

The raw console output is in `logs/wpscan-siteA-cli.txt` and `logs/wpscan-siteB-cli.txt`; the JSON output is in `scans/siteA.json` and `scans/siteB.json`.

---

## 7. WPScan results

### 7.1 Site A – WordPress 4.0.38

WPScan identified the core from the RSS generator with 100% confidence and reported:

```
[+] WordPress version 4.0.38 identified (Insecure, released on 2022-11-30).
```

The version record carried **no individual vulnerability advisories**. The scan reported the following findings:

| Finding | Detail |
|---|---|
| Server headers | `Apache/2.4.58 (Unix) OpenSSL/1.1.1w PHP/8.2.12 mod_perl/2.0.12 Perl/v5.34.1`; `X-Powered-By: PHP/8.2.12` |
| XML-RPC | Enabled at `/siteA/xmlrpc.php` |
| Readme | `/siteA/readme.html` reachable |
| WP-Cron | External `/siteA/wp-cron.php` reachable |
| Theme | Twenty Fourteen 1.2; latest is 4.5 |
| User | `admin` enumerated through author posts and login error messages |

![Figure 15 – WPScan against Site A](screenshots/16-wpscan-siteA.png){ .tall }

*Figure 15. WPScan output for Site A: version 4.0.38 marked Insecure, the out-of-date Twenty Fourteen theme, and the shared default findings.*

### 7.2 Site B – WordPress 7.1.4

WPScan identified Site B from the RSS generator with 100% confidence and reported:

```
[+] WordPress version 7.1.4 identified (Latest, released on 2026-10-28).
```

The version record again carried **no individual vulnerability advisories**. The scan reported:

| Finding | Detail |
|---|---|
| Server headers | `Apache/2.4.58 (Unix) OpenSSL/1.1.1w PHP/8.2.12 mod_perl/2.0.12 Perl/v5.34.1`; `X-Powered-By: PHP/8.2.12` |
| XML-RPC | Enabled at `/siteB/xmlrpc.php` |
| Readme | `/siteB/readme.html` reachable |
| Uploads listing | `/siteB/wp-content/uploads/` directory listing enabled |
| WP-Cron | External `/siteB/wp-cron.php` reachable |
| Theme | Twenty Twenty-Five 1.5; current |
| User | `admin` enumerated through RSS, REST API, user sitemap, author ID pattern and login error messages |

![Figure 16 – WPScan against Site B](screenshots/17-wpscan-siteB.png){ .tall }

*Figure 16. WPScan output for Site B: version 7.1.4 marked Latest, the current Twenty Twenty-Five theme, and the default findings including uploads directory listing.*

### 7.3 Side-by-side

| Measurement | Site A (4.0.38) | Site B (7.1.4) |
|---|---|---|
| Core status | Insecure | Latest |
| Core release date | 2022-11-30 | 2026-10-28 |
| Version-specific vulnerabilities in WPScan | 0 | 0 |
| Active theme | Twenty Fourteen 1.2 (out of date) | Twenty Twenty-Five 1.5 (current) |
| XML-RPC | Enabled | Enabled |
| `readme.html` | Present | Present |
| External WP-Cron | Enabled | Enabled |
| Uploads directory listing | Not present | Enabled |
| User enumeration | `admin` | `admin` |
| Server banner | Full version disclosure | Full version disclosure |

The two scans therefore produced identical counts of known version-specific vulnerabilities but different lifecycle verdicts. Site A's zero is the zero of a branch whose final release consolidated its historical fixes; Site B's zero is the zero of a release line that is still being maintained. The next section tests that distinction against NVD data.

---

## 8. NVD CVE analysis

I queried the NVD 2.0 API with a virtual CPE match for each exact version:

```bash
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:wordpress:wordpress:4.0.38"
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:wordpress:wordpress:7.1.4"
```

The 4.0.38 query returned **134 CVE records**. The 7.1.4 query returned **0**.

### 8.1 Severity distribution for the 4.0.38 match set

| Severity | Count |
|---|---|
| Critical | 14 |
| High | 37 |
| Medium | 82 |
| Low | 1 |
| **Total** | **134** |

### 8.2 Publication years for the 4.0.38 match set

| Year | CVEs | Year | CVEs |
|---|---|---|---|
| 2015 | 11 | 2021 | 1 |
| 2016 | 21 | 2022 | 3 |
| 2017 | 41 | 2023 | 2 |
| 2018 | 17 | 2024 | 2 |
| 2019 | 22 | 2026 | 1 |
| 2020 | 13 | | |

### 8.3 Representative critical and high entries

| CVE | CVSS | Class |
|---|---|---|
| CVE-2016-10033 | 9.8 | PHPMailer `mailSend()` command injection, reachable through bundled core code |
| CVE-2016-10045 | 9.8 | PHPMailer `isMail` command injection |
| CVE-2017-5611 | 9.8 | SQL injection in `WP_Query` |
| CVE-2019-17669 | 9.8 | Server-side request forgery in URL validation |
| CVE-2019-17670 | 9.8 | Server-side request forgery through Windows path handling |
| CVE-2018-12895 | 8.8 | Directory traversal and code execution through the post thumbnail parameter |
| CVE-2016-4029 | 8.6 | Intranet address bypass through octal/hexadecimal IP notation |
| CVE-2026-87902 | 8.1 | Unauthenticated local file inclusion in `get_page_template()`, leading to RCE |

Keyword classification of the 134 descriptions produced 55 cross-site scripting entries, 10 cross-site request forgery entries, 5 remote code execution entries, 4 SQL injection entries, 4 SSRF entries, 4 traversal entries and 4 deserialization entries. The categories overlap because many advisories describe chained effects.

### 8.4 Entries published after 4.0.38

Five records in the match set were published after 4.0.38 shipped on 30 November 2022:

| CVE | Published | Severity | Relationship to the 4.0 branch |
|---|---|---|---|
| CVE-2023-22622 | 2023-01-05 | 5.3 Medium | Describes the dependence of WP-Cron execution and update timing on client visits; the behaviour is present in 4.0.38 |
| CVE-2023-2745 | 2023-05-17 | 5.4 Medium | Directory traversal through the `wp_lang` parameter; fixed in 6.2.1, not in the 4.0 branch |
| CVE-2024-31210 | 2024-04-04 | 7.6 High | Plugin-upload path leading to RCE; backported to 4.1.40 and 4.9.25, not to 4.0 |
| CVE-2022-4973 | 2024-10-16 | 4.9 Medium | Authenticated stored XSS through `the_meta()`; fixed in 6.0.2 before 4.0.38 shipped |
| CVE-2026-87902 | 2026-09-22 | 8.1 High | Unauthenticated template path inclusion leading to RCE; NVD matches 4.0.38 and does not match 7.1.4 |

CVE-2026-87902 is the clearest illustration of the lifecycle gap. It was published on 22 September 2026, six weeks before WordPress 7.1.4 was released, and it is absent from the 7.1.4 match set. The 4.0 branch had already been closed for almost four years when the advisory appeared, so no 4.0.x package contains its fix.

The NVD count and the WPScan count measure different things. WPScan attaches advisories to the exact release that it can confirm and reported none for 4.0.38 because that final release incorporated the fixes available in 2022. NVD matches CPE ranges such as "before 4.5" and therefore keeps historical advisories attached to 4.0.38 even where a backport exists. For the comparison in this report I treated the WPScan result as the count of known unfixed advisories at scan time and the NVD result as the historical exposure profile of the code line. The post-release entries are the overlap where both views agree that no 4.0.x fix exists.

---

## 9. Core security architecture comparison

### 9.1 Lifecycle and patch architecture

Site A is on a closed branch. The dashboard itself states that 4.0.38 is no longer supported and will not receive security updates. The 4.0 line ended with 4.0.38 on 30 November 2022. Every core advisory published after that date is permanently unpatched on Site A unless an administrator manually backports it.

Site B is on the current line. 7.1.4 was released on 28 October 2026 and WPScan classified it as Latest. Its updater includes the `WP_Automatic_Updater` class and the rollback logic that the 4.0 tree does not contain. WordPress 4.0 does have the older `wp_maybe_auto_update()` cron path, but on an ended branch that path has no new package to install.

This is the largest single architectural difference between the two installations. It is not a line of vulnerable code; it is the absence of a supplier.

### 9.2 Password cryptography

| Property | Site A (4.0.38) | Site B (7.1.4) |
|---|---|---|
| Hashing library | `class-phpass.php` | PHP `password_hash()` |
| Algorithm | phpass portable MD5 | bcrypt |
| Stored prefix | `$P$B` | `$wp$2y$10$` |
| Work factor | 8 | 10 |
| Rehash on login | No | Yes, through `wp_password_needs_rehash()` |
| Algorithm filter | None | `wp_hash_password_algorithm` |

The 4.0 hash is a salted MD5 iterated 2^8 times. The 7.1.4 hash is bcrypt with cost 10. The modern core also exposes a filter for the algorithm and supports Argon2 constants where the PHP build provides them. The two records I read from `wp_users` confirmed the difference in the live databases, not only in the source.

### 9.3 Runtime and language compatibility

Site A predates PHP 7 and PHP 8. On PHP 8.2.12 it required the five interventions listed in Section 4.3: mysqli exception suppression, a `get_magic_quotes_gpc()` shim, a `create_function()` shim, a constructor wrapper for phpass, and a corrected `wp_signon()` call. Two of those defects, the phpass constructor and the `wp_signon()` type error, broke authentication outright rather than producing a degraded page.

Site B ran natively. Its code uses typed signatures, attributes such as `#[\SensitiveParameter]`, and the PHP password API directly.

This difference matters for security because a legacy core that cannot execute correctly on a supported PHP runtime cannot receive the runtime's own security fixes without ad hoc patching, and every ad hoc patch widens the gap between the running code and the vendor's signed release.

### 9.4 Attack surface

| Surface | Site A | Site B |
|---|---|---|
| REST API `/wp-json/` | Absent (404) | Present |
| User enumeration through REST | Not available | `admin` returned by `/wp-json/wp/v2/users` |
| User sitemap | Absent | `wp-sitemap-users-1.xml` |
| XML-RPC | Enabled | Enabled |
| `readme.html` | Present | Present |
| External WP-Cron | Enabled | Enabled |
| Uploads directory listing | Not present | Enabled |
| Application passwords | Absent | Present |
| Site Health | Absent | Present |
| Sodium compatibility library | Absent | Present |
| File editors | Present | Present |

The modern core exposes a larger nominal attack surface: a REST API, a user sitemap and application passwords. In this lab the REST API and sitemap both disclosed the `admin` account, and WPScan confirmed the username through five independent methods on Site B. Site A also disclosed `admin`, but through author-post metadata and differentiated login errors rather than a JSON endpoint.

The comparison is therefore not "old core has more endpoints". It is that the modern core has more endpoints **and** a maintained response process, modern password storage, and a runtime that matches the code. The old core has fewer endpoints but no process behind them.

### 9.5 Default configuration weaknesses shared by both

The scans showed that several weaknesses are properties of the default installation rather than of the core generation:

- **XML-RPC enabled.** Both `xmlrpc.php` endpoints answered POST requests with HTTP 200. XML-RPC carries the pingback and brute-force surfaces that WPScan references.
- **Version disclosure.** Both `readme.html` files were reachable, and both RSS feeds emitted `<generator>https://wordpress.org/?v=…</generator>`.
- **WP-Cron reachable over HTTP.** Both `/wp-cron.php` endpoints responded, and WPScan flagged the dependence on external requests for scheduled work.
- **Verbose server headers.** Both responses disclosed the Apache, OpenSSL, PHP, mod_perl and Perl versions, plus `X-Powered-By: PHP/8.2.12`.
- **No HTTP security headers.** Neither site returned HSTS or a content security policy on the plain HTTP vhost.
- **Administrator username `admin`.** Both sites used the same predictable administrator name.

These findings are configuration-level. They appeared on the current core as well as the legacy one, which is why the lifecycle and cryptography differences in Sections 9.1 and 9.2 carry more weight in the comparison than the shared scan findings.

---

## 10. Discussion

The phrase "inherent vulnerability" can mean two different things in a core comparison. It can mean a defect in the source that an attacker can reach, or it can mean a structural property of the release that determines whether defects get fixed.

On the first meaning, the two cores scored the same in WPScan: zero version-specific advisories. That result is accurate for the exact releases. WordPress 4.0.38 was a consolidated security release for the 4.0 line, and WordPress 7.1.4 is the current release. Neither carried an open WPScan advisory at scan time.

On the second meaning, the cores diverged sharply. Site A's branch closed in November 2022. The 4.0.38 archive cannot contain a fix for a vulnerability published in 2023, 2024 or 2026, and three post-release entries in the NVD match set were never backported to 4.0. Site B was six weeks old at the time of the scan and sits on a line that receives fixes, including the fix for CVE-2026-87902.

The runtime evidence pointed the same way. A core that needs a phpass constructor wrapper and a `wp_signon()` call correction to authenticate on PHP 8.2 is not merely old; it is disconnected from the platform it runs on. The modern core used the platform's password API and ran without intervention.

The default configuration evidence cut across both. XML-RPC, `readme.html`, WP-Cron and version banners were present on both sites, and the uploads listing and REST user disclosure were present on the modern site. Those findings show that a current core does not by itself remove configuration exposure; they do not restore parity on the lifecycle and cryptography axes.

My overall finding is that the decisive difference between Site A and Site B is the maintenance architecture. WordPress 4.0.38's inherent weakness is that it cannot be patched, and its MD5-based password storage compounds the consequence of any authentication bypass. WordPress 7.1.4's inherent strength is that it can be patched, stores passwords with bcrypt, and runs on the PHP version it was built for. The scan counts alone would have hidden that difference.

---

## 11. Conclusion

I installed XAMPP, deployed WordPress 4.0.38 and WordPress 7.1.4 as two independent sites, completed both installations, and scanned both with WPScan 4.1.0.

WPScan classified Site A as Insecure (released 30 November 2022) and Site B as Latest (released 28 October 2026). Both scans returned zero version-specific vulnerabilities. Site A's scan exposed an out-of-date Twenty Fourteen 1.2 theme; Site B's scan exposed an enabled uploads directory listing. Both sites exposed XML-RPC, `readme.html`, external WP-Cron, full server banners and the `admin` username.

The NVD comparison separated the two releases. The version range for 4.0.38 matched 134 CVE records (14 critical, 37 high, 82 medium, 1 low). The range for 7.1.4 matched none. Five records were published after 4.0.38 shipped, including CVE-2026-87902 (CVSS 8.1, unauthenticated template inclusion leading to RCE), which NVD matches to 4.0.38 and not to 7.1.4.

The core architecture comparison produced four differences: an ended branch versus a current branch; phpass MD5 cost 8 versus bcrypt cost 10; a core that required five PHP 8.2 compatibility interventions versus one that ran natively; and a larger but maintained modern attack surface versus a smaller but unmaintained legacy one. The shared default exposures showed that configuration risk exists independently of core generation.

---

## Appendix A – Key commands

```bash
# Services
sudo /opt/lampp/lampp start
sudo /opt/lampp/lampp status

# Databases
/opt/lampp/bin/mysql -uroot -e "CREATE DATABASE wp_sitea CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
/opt/lampp/bin/mysql -uroot -e "CREATE DATABASE wp_siteb CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

# Deployment
unzip -q wordpress-4.0.38.zip -d src/siteA
unzip -q wordpress-7.1.4.zip  -d src/siteB
sudo cp -a src/siteA/wordpress /opt/lampp/htdocs/siteA
sudo cp -a src/siteB/wordpress /opt/lampp/htdocs/siteB
sudo chown -R daemon:daemon /opt/lampp/htdocs/siteA /opt/lampp/htdocs/siteB

# Versions
grep -h "wp_version =" src/siteA/wordpress/wp-includes/version.php \
                    src/siteB/wordpress/wp-includes/version.php

# WPScan
wpscan --update
wpscan --url http://localhost/siteA/ --api-token [REDACTED] --enumerate u \
       --random-user-agent --no-banner --format json --output scans/siteA.json
wpscan --url http://localhost/siteB/ --api-token [REDACTED] --enumerate u \
       --random-user-agent --no-banner --format json --output scans/siteB.json

# NVD
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:wordpress:wordpress:4.0.38"
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:wordpress:wordpress:7.1.4"
```

## Appendix B – Artefacts

| Path | Content |
|---|---|
| `scans/siteA.json` | WPScan JSON, Site A |
| `scans/siteB.json` | WPScan JSON, Site B |
| `scans/nvd-wordpress-4.0.38.json` | NVD 2.0 response, 134 records |
| `scans/nvd-wordpress-7.1.4.json` | NVD 2.0 response, 0 records |
| `scans/nvd-wordpress-4.0.38-cves.csv` | 134-row CVE table (ID, date, severity, CVSS, vector, description) |
| `logs/wpscan-siteA-cli.txt` | Console capture, Site A |
| `logs/wpscan-siteB-cli.txt` | Console capture, Site B |
| `logs/wpscan-siteA-shot.txt` | Annotated console capture used for Figure 15 |
| `logs/wpscan-siteB-shot.txt` | Annotated console capture used for Figure 16 |
| `screenshots/01-17` | Evidence images used in this report |

## Appendix C – Host and application versions

| Component | Version |
|---|---|
| Kali GNU/Linux | Rolling 2026.2 |
| Kernel | 7.1.5+kali-amd64 |
| XAMPP for Linux | 8.2.12-0 |
| Apache | 2.4.58 (Unix) |
| MariaDB | 10.4.32 |
| PHP | 8.2.12 |
| OpenSSL | 1.1.1w |
| phpMyAdmin | 5.2.1 |
| WPScan | 4.1.0 |
| WordPress Site A | 4.0.38 |
| WordPress Site B | 7.1.4 |
