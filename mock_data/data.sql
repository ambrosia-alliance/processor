INSERT INTO therapies (id, name, cost_summary, cost_currency, cost_amount, cost_citation_ids) VALUES
(1, 'Therapeutic Plasma Exchange', 'Average cost per session ranges from $500-800. Complete therapy course (5 sessions) typically costs $2,500-4,000 in US facilities.', 'USD', 3250.00, '[2, 3]');

INSERT INTO articles (id, therapy_id, title, journal, year, url, doi) VALUES
(1, 1, 'Therapeutic Plasma Exchange for Longevity: A Randomized Controlled Trial', 'Journal of Gerontology and Aging', 2024, 'https://example.com/jga-2024-plasma', '10.1000/jga.2024.001'),
(2, 1, 'Safety and Efficacy of Plasma Exchange in Healthy Aging Adults', 'Clinical Interventions in Aging', 2024, 'https://example.com/cia-2024-safety', '10.1000/cia.2024.045'),
(3, 1, 'Biomarker Changes Following Therapeutic Plasma Exchange', 'Aging Cell', 2024, 'https://example.com/aging-cell-2024', '10.1000/agingcell.2024.089');

INSERT INTO citations (id, quote_text, article_id, locator) VALUES
(1, 'Therapeutic plasma exchange reduced inflammatory biomarkers by 35% after 4 weeks of therapy.', 3, 'Table 2, p. 445'),
(2, 'The procedure costs approximately $500-800 per session in most US facilities.', 1, 'p. 12'),
(3, 'Total therapy cost including 5 sessions ranged from $2,500 to $4,000.', 1, 'Discussion section'),
(4, '67% of participants showed measurable improvements in longevity markers including NAD+ and epigenetic clock measurements.', 1, 'Results, p. 234'),
(5, 'Response rate was observed in 72 out of 108 participants (66.7%) at 12-week follow-up.', 1, 'Figure 3'),
(6, 'Most common adverse events were mild hypotension and temporary fatigue, occurring in 15% of sessions.', 2, 'Adverse Events section'),
(7, 'Severe complications including allergic reactions were rare, occurring in 0.8% of all procedures.', 2, 'Meta-analysis results'),
(8, 'Risk of infection or catheter-related complications was 2.3% across all therapy centers.', 2, 'Table 4'),
(9, 'The study enrolled 108 participants aged 50-75 years from three clinical centers.', 1, 'Methods'),
(10, 'Participant demographics: 58% female, 42% male, mean age 62.4 years.', 1, 'Baseline characteristics'),
(11, 'This was a randomized, double-blind, sham-controlled trial with 24-week follow-up.', 1, 'Study Design'),
(12, 'Improvements in cognitive function scores averaged 18% above baseline after 12 weeks.', 1, 'Primary outcomes'),
(13, 'Open-label safety study with 12-week observation period assessing adverse events.', 2, 'Methods section'),
(14, 'Study enrolled 45 participants aged 45-70 years at single clinical center.', 2, 'Table 1'),
(15, 'Participant breakdown: 24 female (53%), 21 male (47%).', 2, 'Baseline data'),
(16, 'Age distribution: mean 58.7 years, median 59 years, range 45-70 years.', 2, 'Demographics table'),
(17, 'Prospective cohort study design with 16-week biomarker monitoring protocol.', 3, 'Study design'),
(18, 'Cohort of 76 participants recruited from community aging centers.', 3, 'Recruitment section'),
(19, 'Sex distribution: 60% female (n=46), 40% male (n=30).', 3, 'Table 2'),
(20, 'Mean participant age was 65.2 years (SD 6.3), range 55-78 years.', 3, 'Demographics');

INSERT INTO article_details (article_id, design_summary, design_citation_ids, participants_total, participants_citation_ids, sex_summary, sex_citation_ids, age_summary, age_citation_ids) VALUES
(1, 'Randomized, double-blind, sham-controlled trial with 24-week follow-up period', '[11]', 108, '[9]', '58% female, 42% male', '[10]', 'Mean age 62.4 years, range 50-75', '[10]'),
(2, 'Open-label safety study with 12-week observation period', '[13]', 45, '[14]', '53% female, 47% male', '[15]', 'Mean age 58.7 years, range 45-70', '[16]'),
(3, 'Prospective cohort study measuring biomarker changes over 16 weeks', '[17]', 76, '[18]', '60% female, 40% male', '[19]', 'Mean age 65.2 years, range 55-78', '[20]');

INSERT INTO effects (id, therapy_id, name, efficacy_extent_summary, efficacy_extent_citation_ids, efficacy_rate_summary, efficacy_rate_citation_ids, side_effect_severity_summary, side_effect_severity_citation_ids, side_effect_risk_summary, side_effect_risk_citation_ids, participants_total, sex_summary, age_summary, design_summaries) VALUES
(1, 1, 'Reduction in inflammatory biomarkers', 'Inflammatory biomarkers (CRP, IL-6) reduced by 35% after 4 weeks. Cognitive function improved by 18% above baseline after 12 weeks.', '[1, 12]', '67% of participants showed measurable improvements in longevity markers (NAD+, epigenetic clock). Overall response rate was 66.7% at 12-week follow-up.', '[4, 5]', NULL, '[]', NULL, '[]', 229, '57% female, 43% male', 'Mean age 62.1 years, range 45-78', '["Randomized controlled trial", "Open-label safety study", "Prospective cohort study"]'),
(2, 1, 'Mild procedural side effects', NULL, '[]', NULL, '[]', 'Most common adverse events were mild hypotension and temporary fatigue, typically resolving within 24 hours. Generally well-tolerated with manageable side effects.', '[6]', '15% of therapy sessions resulted in mild adverse events. Most were transient and required no intervention.', '[6]', 229, '57% female, 43% male', 'Mean age 62.1 years, range 45-78', '["Randomized controlled trial", "Open-label safety study", "Prospective cohort study"]'),
(3, 1, 'Serious complications', NULL, '[]', NULL, '[]', 'Severe complications including allergic reactions were rare but potentially serious. Catheter-related issues occurred in small percentage of cases.', '[7]', 'Risk of severe allergic reactions: 0.8%. Risk of infection or catheter complications: 2.3%. Overall serious complication rate under 3%.', '[7, 8]', 229, '57% female, 43% male', 'Mean age 62.1 years, range 45-78', '["Randomized controlled trial", "Open-label safety study", "Prospective cohort study"]');

SELECT setval('citations_id_seq', (SELECT MAX(id) FROM citations));
SELECT setval('therapies_id_seq', (SELECT MAX(id) FROM therapies));
SELECT setval('articles_id_seq', (SELECT MAX(id) FROM articles));
SELECT setval('effects_id_seq', (SELECT MAX(id) FROM effects));

