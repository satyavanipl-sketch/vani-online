# VaniOnline Content-Generation Workflow Rules

These permanent rules apply to all NEW blog posts created on VaniOnline.com. Do not modify existing published posts.

## 1. Content Length, Sentence Structure & Humanized Tone
*   **Standard children's story:** Target 600 to 800 words.
*   **Simple preschool story:** 450 to 600 words is acceptable.
*   **Detailed moral, adventure, or educational story:** 700 to 900 words is acceptable when the story needs more depth.
*   **Strictly Humanized Writing:** All text must be 100% humanized, warm, engaging, and natural for parents reading aloud to young children. Avoid dry AI filler, awkward repetitions, or mechanical phrasing.
*   **Flesch Reading Ease (>65 Target):** Keep sentences short (8 to 12 words per sentence) for high readability and easy comprehension for children and parents.

## 2. Recommended Article Structure
Where appropriate, structure new stories as follows:
1.  **Introduction:** SEO-friendly hook, approximately 50 to 70 words, embedding the primary focus keyword.
2.  **Story Highlights Box:** High-contrast summary box detailing Character, Core Lesson, and Best For age range.
3.  **Main Story Sections:** Clear `<h2>` subheadings **without number prefixes** (e.g. use `The Quiet Turtle of Whispering Creek`, NOT `1. The Quiet...`). Include the focus keyword in at least 30% of `<h2>` or `<h3>` subheadings.
4.  **Moral of the Story:** Summary of the core lesson, approximately 40 to 70 words.
5.  **What Children Learn:** Clear takeaways, approximately 30 to 50 words.
6.  **Interactive Questions:** 2 to 3 simple discussion questions for kids.
7.  **Educational Resources:** Section with at least 2 authoritative external links.
8.  **Read Next:** Section containing exactly 3 relevant internal links to existing VaniOnline stories.

## 3. SEO & AIOSEO Requirements
*   **Primary Focus Keyword:** Select one clear, story-specific focus keyword based on the character, moral theme, or age group.
    *   *Examples:* `kindness story for kids`, `honesty story for kids`, `sharing story for kids`, `courage story for kids`, `animal story for kids`, `ganesha story for kids`, `turtle story for kids`, `bedtime stories for kindergarten`, `moral story for kids`.
*   **Focus Keyword in URL Slug:** The URL permalink slug **must explicitly contain the exact Focus Keyword** (e.g. `lord-ganesha-story-for-kids-wisdom-and-love` containing `ganesha-story-for-kids`).
*   **Focus Keyword Position in SEO Title:** Always place the Focus Keyword at or near the **beginning of the SEO Title** (e.g. `[Focus Keyword]: [Story Name] - [Power Word] [Type]`). Target 50 to 60 characters (max 60 recommended limit).
*   **Blog Title (Headline Analyzer Score > 70):** The WP Post Title (`post_title`) must include a **Power Word** (e.g. `Best`, `Amazing`, `Delightful`, `Ultimate`) and an **Emotional/Sentiment Word** (e.g. `Inspiring`, `Courage`, `Brave`, `Heartwarming`, `Wisdom`), targeting a score **> 70 / 100**.
    *   **No Emojis in Blog Title:** Do NOT include emojis inside the `post_title` string (e.g. use `Lord Ganesha: Best Inspiring Wisdom Story for Kids`, NOT `... 🐘✨`) because Headline Analyzer penalizes non-ASCII emoji symbols below 70.
*   **Focus Keyword in Subheadings:** Include the primary focus keyword in at least 30% of `<h2>` or `<h3>` subheadings.
*   **Focus Keyword Density:** Maintain a focus keyword density of **0.5% to 1.5%** naturally across the text (4 to 6 natural occurrences in a 600-800 word story).
*   **Meta Description:** Target 140 to 160 characters with a unique, natural description incorporating the focus keyword.
*   **AIOSEO Database Score Sync:** When saving or updating via API, populate `seo_score: 100` and `keyphrases["focus"]["score"]: 100` with complete 8-point `analysis` metrics so the WP Posts list table displays a green **`[⚙ 100/100]`** badge.

## 4. Readability & Transition Words (>30% Target)
*   **Transition Words Requirement:** At least **30% of all sentences** must contain natural transition words (*however, suddenly, gentle, as a result, at the same time, eventually, for example, for instance, furthermore, in addition, also, next, finally, soon, step by step, indeed, in conclusion, moreover, because, therefore, meanwhile*).
*   **Paragraph Length:** Use short paragraphs (2 to 3 sentences maximum) for easy mobile reading.

## 5. Internal & External Linking
*   **Internal Links:** Include **approximately 3 relevant internal links** to existing VaniOnline stories in the "Read Next" section.
*   **External Links:** Include at least **2 authoritative external links** to reputable educational/wildlife platforms (e.g. National Geographic Kids, PBS KIDS, Scholastic).

## 6. Image Requirements & Layout
*   **Standard Count:** Generate exactly **6 images** by default (Featured cover + 4 story scenes + 1 ending scene).
*   **Visual Consistency:** Maintain strict character appearance, clothing, art style, and setting consistency across all story illustrations (e.g. exactly one single main character per scene).
*   **Alternating Image Alignment:** Story images inside article sections must strictly alternate alignment: if Image is on **Left Float** (Image 1, 3, 5), story text flows on the **Right** (`float: left !important; margin: 10px 25px 20px 0 !important;`); if Image is on **Right Float** (Image 2, 4), story text flows on the **Left** (`float: right !important; margin: 10px 0 20px 25px !important;`). Use rounded corners (`border-radius: 24px !important;`), soft shadows, clean margins, and `clear: both !important;` on subheadings so text wraps around elegantly without overlapping.
*   **SEO & ALT Tags:** Every image must be in optimized **WebP format** with descriptive ALT text incorporating the story focus keyphrase naturally.

---

## 📋 Pre-Publishing AIOSEO Checklist
Before scheduling or publishing any post, verify:
- [ ] Word count is in target range (600–800 words) with 100% humanized, natural tone.
- [ ] Sentences are short (8-12 words) for Flesch Reading Ease score > 65.
- [ ] Focus keyword is present in the URL slug (`ganesha-story-for-kids`).
- [ ] SEO Title begins with the Focus Keyword and targets 50–60 characters.
- [ ] Blog Title includes Power & Emotion words scoring > 70 on Headline Analyzer (no emojis in `post_title`).
- [ ] Subheadings do NOT contain number prefixes (e.g. no `1.`, `2.`, `3.`).
- [ ] Focus keyword appears in the Introduction paragraph.
- [ ] Focus keyword appears in at least 30% of `<h2>` or `<h3>` Subheadings.
- [ ] Focus keyword density is between 0.5% and 1.5%.
- [ ] Over 30% of sentences contain natural transition words.
- [ ] Meta description is a unique 140–160 character snippet with focus keyword.
- [ ] Exactly 3 relevant internal links are included in "Read Next".
- [ ] At least 2 authoritative external links are included.
- [ ] 6 WebP images with custom ALT text, character visual consistency, and alternating Left/Right layout.
- [ ] AIOSEO database record updated with 100/100 score analysis.
