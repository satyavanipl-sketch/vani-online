# VaniOnline Master SEO Audit & Pre-Publishing Report Standard

This document outlines the mandatory 11-point AIOSEO Audit Checklist that must be evaluated and verified for **all future blog posts** on VaniOnline.com.

---

## 📋 Master 11-Point AIOSEO Audit Checklist

| Item # | Audit Parameter | Technical Standard & Requirement | Weight / Points |
|---|---|---|---|
| **1** | **AIOSEO Focus Keyphrase** | Set a unique, story-specific focus keyphrase in AIOSEO (e.g. `courage story for kids`, `kindness story for kids`, `ganesha story for kids`). | **15 pts** |
| **2** | **WP Blog Title (`post_title`)** | Must score **> 70 / 100** on Headline Analyzer by including a **Power Word** (`Best`, `Amazing`, `Delightful`, `Ultimate`) and an **Emotion Word** (`Inspiring`, `Courage`, `Brave`, `Heartwarming`, `Wisdom`). **Avoid emojis in title string.** | **15 pts** |
| **3** | **SEO Meta Title & Keyword Position** | Always place the **Focus Keyword at the very beginning** of the SEO Title string (`[Focus Keyword]: [Story Name] - [Type]`). Target **50 to 60 characters** (maximum 60 recommended characters limit). | **10 pts** |
| **4** | **Focus Keyword in URL Slug** | The post permalink URL slug must explicitly contain the focus keyphrase (e.g. `lord-ganesha-story-for-kids-wisdom-and-love`). | **10 pts** |
| **5** | **Subheading Keyword & No Numbers** | **Strict Requirement:** Subheadings must **NOT** contain number prefixes (no `1.`, `2.`, `3.`) and at least 30% of `<h2>` subheadings must contain the focus keyword. | **10 pts** |
| **6** | **Readability & Transition Words** | At least **> 30% of all sentences** must contain natural transition words (*however, suddenly, gentle, as a result, at the same time, eventually, for example, furthermore, in addition, also, next, finally, soon, step by step, indeed, in conclusion, moreover*). Flesch Reading Ease score **> 65**. | **10 pts** |
| **7** | **Meta Description** | Target **140 to 160 characters** containing a unique, natural snippet embedding the primary focus keyword. | **10 pts** |
| **8** | **SEO Meta Title Length Limit** | Strict length check: SEO Title must be **<= 60 characters** (green status in AIOSEO UI). | **5 pts** |
| **9** | **Meta Description Length Range** | Strict length check: Meta description must be **140 to 160 characters**. | **5 pts** |
| **10** | **Image SEO, WebP & Alternating Layout** | 100% of images must be in **WebP format** with descriptive **ALT tags**. Images must alternate: Image Left -> Text Right (Images 1, 3, 5) and Image Right -> Text Left (Images 2, 4) with `clear: both !important;` on subheadings. | **5 pts** |
| **11** | **Authoritative External & Internal Links** | Include at least **2 authoritative external links** (e.g. National Geographic Kids, PBS KIDS) and **~3 relevant internal links** in the "Read Next" section. | **5 pts** |

---

## 🛠️ Automated Audit Tool for Future Blogs

Run the automated CLI audit tool on any published or draft post ID:

```bash
python3 audit_future_blog_seo.py <POST_ID>
```

**Example Execution:**
```bash
python3 audit_future_blog_seo.py 320883
```

**Verified Output (100% Score):**
```text
=================================================================
        VANI ONLINE MASTER SEO AUDIT REPORT FOR POST #320883
=================================================================
[1] METADATA & TITLE ANALYSIS:
  - Post Status           : FUTURE (Scheduled for 2026-09-10T10:00:00)
  - Focus Keyword         : 'ganesha story for kids'
  - WP Blog Title (H1)     : 'Lord Ganesha: Best Inspiring Wisdom Story for Kids' (50 chars)
  - Blog Title Score (>70) : PASS (Power & Emotion Words Present)
  - SEO Meta Title         : 'Ganesha Story for Kids: Little Ganesha's Best Tale' (50 chars)
  - SEO Title Length (<=60): PASS
  - Keyphrase at Beginning : PASS
  - Meta Description       : 'Read this heartwarming Ganesha story for kids about little Lord Ganesha's gentle wisdom and love for his parents. Inspiring bedtime moral tale.' (143 chars)

[2] HEADING STRUCTURE & SUBHEADINGS:
  - Total H2 Headings      : 10
  - Keyword in Subheadings : PASS (4/10 = 40% >= 30% target)
  - Numbered Headings Check: PASS (No numbers in subheadings)

[3] CONTENT QUALITY & READABILITY:
  - Word Count             : 689 words
  - Transition Words %     : 33.8% (22/65) -> PASS (>30%)

[4] LINKING & MEDIA AUDIT:
  - Internal Links Count   : 3 -> PASS (~3 links)
  - External Links Count   : 2 -> PASS (>=2 links)
  - Story Images (WebP/ALT): 5 Total | 5 WebP | 5 ALT Tags

=================================================================
            FINAL MASTER SEO SCORE: 100 / 100 (100.0%)
=================================================================
  [✔] AIOSEO Focus Keyphrase Set (+15/15 pts)
  [✔] Blog Title Headline Analyzer Score > 70 (+15/15 pts)
  [✔] Focus Keyword at Beginning of SEO Title (+10/10 pts)
  [✔] Focus Keyword in H2/H3 Subheadings (+10/10 pts)
  [✔] Subheadings Free of Number Prefixes (No 1., 2., 3.) (+10/10 pts)
  [✔] Readability Transition Words > 30% (+10/10 pts)
  [✔] Keyphrase in Meta Description (+10/10 pts)
  [✔] SEO Title Length <= 60 characters (+5/5 pts)
  [✔] Meta Description Length (140-160 chars) (+5/5 pts)
  [✔] 100% WebP Story Images with Custom ALT Text (+5/5 pts)
  [✔] Authoritative External Links (>= 2 links) (+5/5 pts)
=================================================================

[AIOSEO DB SYNC]: Successfully synced score 100/100 to WordPress DB!
```
