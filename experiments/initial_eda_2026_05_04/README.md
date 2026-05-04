# Initial EDA

Initial list of EDA tasks that we want to run:

1. Language mix among user turns: Which languages dominate user queries, and what share is English vs everything else?
2. First user turn vs later user turn: Distinguishes task initiation (what people open with) from repair, clarification, and negotiation—core concepts in conversation analysis and HCI. Can use basic keyword exact lookups to determine user intent and topic. Should look at length and intent and topic.
3. Thread length (turns_count) vs user-turn properties: Long threads often indicate troubleshooting, emotional support, or iterative co-production—distinct social modes of use. Question: Are longer conversations associated with longer user messages, certain languages, or topics? Bin turns_count (e.g., 1–2, 3–5, 6+); within bins, summarize user plain_text length or topic/language shares; Spearman correlation as a one-liner sanity check.
4. Self-reference vs other-reference (pronoun ratios): How often do users center “I/me/my” vs “they/them” or “you” (the bot)?  Simple regex or token-based counts on lowercased plain_text; ratios or counts per message.
5. Interrogativity and “help-seeking” surface cues: Questions vs statements signal information-seeking, instruction requests, and asymmetry in human–assistant roles—lightweight pragmatics. Question: What fraction of user turns end with ?, or contain “how/why/what/should/can you”? Boolean columns via str.contains with case=False, na=False; report rates overall and by language or topic.
