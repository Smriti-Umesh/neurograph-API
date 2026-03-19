import os
import re
import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
NETWORK_NAME = os.getenv("PUBMED_NETWORK_NAME", "PubMed Knowledge Graph")
PUBMED_QUERY = os.getenv("PUBMED_QUERY", "hebbian learning")
PUBMED_MAX_RECORDS = int(os.getenv("PUBMED_MAX_RECORDS", "5"))
INGESTION_STATE_PATH = os.getenv("PUBMED_STATE_PATH", "data/pubmed_ingestion_state.json")
PUBMED_REINGEST_MODE = os.getenv("PUBMED_REINGEST_MODE", "new_only").strip().lower()
API_USERNAME = os.getenv("API_USERNAME", "")
API_PASSWORD = os.getenv("API_PASSWORD", "")
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


# Global variable to cache the access token for API authentication
ACCESS_TOKEN: Optional[str] = None


def login_and_get_token() -> str:
    if not API_USERNAME or not API_PASSWORD:
        raise ValueError(
            "Missing API_USERNAME or API_PASSWORD in environment. "
            "Set them in .env so the ingestion script can authenticate."
        )

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": API_USERNAME,
            "password": API_PASSWORD,
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise ValueError("Login succeeded but no access_token was returned.")

    return token

def get_auth_headers() -> Dict[str, str]:
    global ACCESS_TOKEN

    if ACCESS_TOKEN is None:
        ACCESS_TOKEN = login_and_get_token()

    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

# filtering out some very common stopwords and generic phrases that often get extracted as concepts but aren't meaningful for graph connections
COMMON_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "were", "with", "we", "our", "using", "use", "used", "via", "than", "these",
    "those", "can", "may", "such", "during", "within", "across", "allows", "allow"
}

BORING_PHRASES = {
    "in this study",
    "this study",
    "we show",
    "we found",
    "we propose",
    "results suggest",
    "our results",
    "our findings",
    "in conclusion",
    "the results",
    "the present study",
    "this paper",
    "this work",
    "these results",
    "the authors",
}

# normalization and cleaning helpers

def clean_text(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_text(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_author_name(name: str) -> str:
    name = normalize_text(name)
    name = name.replace(".", "")
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_journal_name(name: str) -> str:
    return normalize_text(name)


def normalize_concept_name(name: str) -> str:
    return normalize_text(name)


def build_paper_label(title: str, pmid: Optional[str]) -> str:
    clean_title = clean_text(title)
    if pmid:
        return f"Paper[{pmid}]: {clean_title}"
    return f"Paper: {clean_title}"


def build_author_label(author: str) -> str:
    return f"Author: {clean_text(author)}"


def build_journal_label(journal: str) -> str:
    return f"Journal: {clean_text(journal)}"


def build_concept_label(concept: str) -> str:
    return clean_text(concept)


def make_paper_key(title: str, pmid: Optional[str]) -> str:
    if pmid:
        return f"paper:pmid:{pmid}"
    return f"paper:title:{normalize_text(title)}"


def make_author_key(author: str) -> str:
    return f"author:{normalize_author_name(author)}"


def make_journal_key(journal: str) -> str:
    return f"journal:{normalize_journal_name(journal)}"


def make_concept_key(concept: str) -> str:
    return f"concept:{normalize_concept_name(concept)}"

# Key generation helper based on existing node data, to avoid creating duplicates when the same paper/author/journal/concept is encountered multiple times in the ingestion process
def make_key_from_existing_node(node: Dict) -> str:
    label = node["label"]
    node_type = node["node_type"]

    if node_type == "paper":
        match = re.match(r"^Paper\[(.+?)\]:\s*(.+)$", label)
        if match:
            pmid = match.group(1).strip()
            title = match.group(2).strip()
            return make_paper_key(title, pmid)

        if label.startswith("Paper:"):
            title = label.replace("Paper:", "", 1).strip()
            return make_paper_key(title, None)

        return f"paper:label:{normalize_text(label)}"

    if node_type == "author":
        author = label.replace("Author:", "", 1).strip()
        return make_author_key(author)

    if node_type == "journal":
        journal = label.replace("Journal:", "", 1).strip()
        return make_journal_key(journal)

    if node_type == "concept":
        return make_concept_key(label)

    return f"{node_type}:{normalize_text(label)}"

# Concept phrase validation to filter out very generic or uninformative phrases that often get extracted from text but don't make good graph nodes
def is_valid_concept_phrase(phrase: str) -> bool:
    cleaned = clean_text(phrase)
    normalized = normalize_text(cleaned)

    if not normalized:
        return False

    if normalized in BORING_PHRASES:
        return False

    words = normalized.split()

    if len(words) == 0 or len(words) > 4:
        return False

    if all(word in COMMON_STOPWORDS for word in words):
        return False

    if len(words) == 1 and len(words[0]) < 4:
        return False

    if any(char.isdigit() for char in normalized):
        return False

    # Reject phrases that start or end with stopwords
    if words[0] in COMMON_STOPWORDS or words[-1] in COMMON_STOPWORDS:
        return False

    # Reject phrases with too many stopwords overall
    stopword_count = sum(1 for word in words if word in COMMON_STOPWORDS)
    if stopword_count > 1:
        return False

    # Reject very generic leading words
    bad_starts = {"this", "these", "those", "different", "various", "present"}
    if words[0] in bad_starts:
        return False

    # Reject very generic trailing words
    bad_ends = {"study", "paper", "result", "results", "subjects", "patients"}
    if words[-1] in bad_ends:
        return False

    return True


def extract_text_concepts(title: Optional[str], abstract: Optional[str], max_concepts: int = 8) -> List[str]:
    source_parts = []

    if title:
        source_parts.append(title)


    if abstract:
        source_parts.append(abstract)

    if not source_parts:
        return []

    text = " ".join(source_parts)
    text = text.replace("/", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace(":", " ")
    text = text.replace(";", " ")
    text = text.replace(",", " ")
    text = re.sub(r"[^A-Za-z0-9\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    candidates = []
    seen = set()

    # Prefer 3-word and 2-word phrases first, then 1-word fallback
    for n in (3, 2, 1):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i:i+n])
            normalized = normalize_concept_name(phrase)

            if normalized in seen:
                continue

            if is_valid_concept_phrase(phrase):
                seen.add(normalized)
                candidates.append(clean_text(phrase))

    # Prefer phrases that contain at least one longer word,
    # which often makes them more concept-like
    candidates.sort(
        key=lambda phrase: (
            -len(phrase.split()),
            -max(len(word) for word in phrase.split())
        )
    )

    return candidates[:max_concepts]

# PubMed API interaction helpers

def search_pubmed(query: str, max_records: int) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_records,
        "retmode": "json",
    }

    response = requests.get(ESEARCH_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data["esearchresult"].get("idlist", [])


def fetch_pubmed_details(pmids: List[str]) -> str:
    if not pmids:
        return ""

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    response = requests.get(EFETCH_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.text


# XML parsing helpers

def get_text(element: Optional[ET.Element]) -> Optional[str]:
    if element is None:
        return None
    text = "".join(element.itertext()).strip()
    return text if text else None


def parse_article(article_elem: ET.Element) -> Dict:
    medline = article_elem.find("MedlineCitation")
    article = medline.find("Article") if medline is not None else None

    title = get_text(article.find("ArticleTitle")) if article is not None else None

    abstract_parts = []
    if article is not None:
        abstract = article.find("Abstract")
        if abstract is not None:
            for part in abstract.findall("AbstractText"):
                text = get_text(part)
                if text:
                    abstract_parts.append(text)

    abstract_text = " ".join(abstract_parts) if abstract_parts else None

    authors = []
    if article is not None:
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                collective_name = get_text(author.find("CollectiveName"))
                if collective_name:
                    authors.append(collective_name)
                    continue

                fore_name = get_text(author.find("ForeName"))
                last_name = get_text(author.find("LastName"))

                if fore_name and last_name:
                    authors.append(f"{fore_name} {last_name}")
                elif last_name:
                    authors.append(last_name)

    journal = get_text(article.find("Journal/Title")) if article is not None else None
    pmid = get_text(medline.find("PMID")) if medline is not None else None

    mesh_terms = []
    mesh_heading_list = medline.find("MeshHeadingList") if medline is not None else None
    if mesh_heading_list is not None:
        for mesh_heading in mesh_heading_list.findall("MeshHeading"):
            descriptor = get_text(mesh_heading.find("DescriptorName"))
            if descriptor:
                mesh_terms.append(descriptor)

    keywords = []
    if medline is not None:
        for keyword_list in medline.findall("KeywordList"):
            for keyword in keyword_list.findall("Keyword"):
                text = get_text(keyword)
                if text:
                    keywords.append(text)

    pubmed_concepts = list(dict.fromkeys(mesh_terms + keywords))
    text_concepts = extract_text_concepts(title, abstract_text)

    all_concepts = list(dict.fromkeys(pubmed_concepts + text_concepts))

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract_text,
        "authors": authors,
        "journal": journal,
        "concepts": all_concepts,
        "pubmed_concepts": pubmed_concepts,
        "text_concepts": text_concepts,
    }


def parse_pubmed_xml(xml_text: str) -> List[Dict]:
    if not xml_text.strip():
        return []

    root = ET.fromstring(xml_text)
    articles = []

    for pubmed_article in root.findall("PubmedArticle"):
        parsed = parse_article(pubmed_article)
        if parsed.get("title"):
            articles.append(parsed)

    return articles

def build_ingestion_state_key(network_name: str, query: str) -> str:
    return f"{network_name}::{normalize_text(query)}"

# network/query-specific ingestion state 
# management to track which PMIDs 
# have already been ingested for a given network and query, 
# allowing the script to skip already processed papers on 
# subsequent runs when using "new_only" mode

def build_ingestion_state_key(network_name: str, query: str) -> str:
    return f"{network_name}::{normalize_text(query)}"


def load_ingestion_state() -> Dict[str, List[str]]:
    if not os.path.exists(INGESTION_STATE_PATH):
        return {}

    try:
        with open(INGESTION_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_ingestion_state(state: Dict[str, List[str]]) -> None:
    os.makedirs(os.path.dirname(INGESTION_STATE_PATH), exist_ok=True)

    with open(INGESTION_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_seen_pmids(network_name: str, query: str) -> set[str]:
    state = load_ingestion_state()
    state_key = build_ingestion_state_key(network_name, query)
    return set(state.get(state_key, []))


def add_seen_pmids(network_name: str, query: str, pmids: List[str]) -> None:
    state = load_ingestion_state()
    state_key = build_ingestion_state_key(network_name, query)

    existing = set(state.get(state_key, []))
    existing.update(pmids)

    state[state_key] = sorted(existing)
    save_ingestion_state(state)

def list_networks() -> List[Dict]:
    response = requests.get(
        f"{BASE_URL}/networks/",
        headers=get_auth_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def create_network(name: str) -> Dict:
    payload = {"name": name}
    response = requests.post(
        f"{BASE_URL}/networks/",
        json=payload,
        headers=get_auth_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_or_create_network_id(network_name: str) -> int:
    networks = list_networks()

    for network in networks:
        if network["name"] == network_name:
            print(f"Using existing network: {network_name} (id={network['id']})")
            return network["id"]

    network = create_network(network_name)
    print(f"Created network: {network_name} (id={network['id']})")
    return network["id"]


# Node and edge management helpers

def get_existing_nodes(network_id: int) -> Dict[str, int]:
    response = requests.get(
        f"{BASE_URL}/networks/{network_id}/nodes",
        headers=get_auth_headers(),
        timeout=30,
    )
    response.raise_for_status()
    nodes = response.json()

    node_map = {}
    for node in nodes:
        key = make_key_from_existing_node(node)
        node_map[key] = node["id"]

    return node_map


def create_node(network_id: int, label: str, node_type: str) -> int:
    payload = {
        "label": label,
        "node_type": node_type,
    }

    response = requests.post(
        f"{BASE_URL}/networks/{network_id}/nodes",
        json=payload,
        headers=get_auth_headers(),
        timeout=30,
    )
    response.raise_for_status()

    node = response.json()
    print(f"Created node: {label} (id={node['id']}, type={node_type})")
    return node["id"]


def ensure_node(
    network_id: int,
    node_map: Dict[str, int],
    key: str,
    label: str,
    node_type: str,
) -> int:
    if key not in node_map:
        node_map[key] = create_node(network_id, label, node_type)
    return node_map[key]


# Edge management helper to create a relationship between two nodes,
# with a specified relationship type, and handle API 
# interaction and error checking

def learn_edge(
    network_id: int,
    source_id: int,
    target_id: int,
    relationship_type: str,
) -> None:
    payload = {
        "source_node_id": source_id,
        "target_node_id": target_id,
        "relationship_type": relationship_type,
    }

    response = requests.post(
        f"{BASE_URL}/networks/{network_id}/learn",
        json=payload,
        headers=get_auth_headers(),
        timeout=30,
    )
    response.raise_for_status()

    print(f"Learned: {source_id} -> {target_id} ({relationship_type})")


# and then the main ingestion logic that ties everything together,
# fetching data from PubMed, parsing it, and creating nodes and edges in the graph based
# on the article metadata and extracted concepts

def ingest_article(network_id: int, node_map: Dict[str, int], article: Dict) -> None:
    title = article.get("title")
    pmid = article.get("pmid")

    if not title:
        return

    paper_label = build_paper_label(title, pmid)
    paper_key = make_paper_key(title, pmid)
    paper_id = ensure_node(network_id, node_map, paper_key, paper_label, "paper")

    journal = article.get("journal")
    if journal:
        journal_label = build_journal_label(journal)
        journal_key = make_journal_key(journal)
        journal_id = ensure_node(network_id, node_map, journal_key, journal_label, "journal")
        learn_edge(network_id, paper_id, journal_id, "published_in")

    for author in article.get("authors", []):
        if not author:
            continue
        author_label = build_author_label(author)
        author_key = make_author_key(author)
        author_id = ensure_node(network_id, node_map, author_key, author_label, "author")
        learn_edge(network_id, paper_id, author_id, "authored_by")

    for concept in article.get("concepts", []):
        if not concept:
            continue
        concept_label = build_concept_label(concept)
        concept_key = make_concept_key(concept)
        concept_id = ensure_node(network_id, node_map, concept_key, concept_label, "concept")
        learn_edge(network_id, paper_id, concept_id, "mentions")

def link_similar_papers(network_id: int, node_map: Dict[str, int], articles: List[Dict]) -> None:
    paper_concepts: Dict[int, set[str]] = {}

    for article in articles:
        title = article.get("title")
        pmid = article.get("pmid")

        if not title:
            continue

        paper_key = make_paper_key(title, pmid)
        paper_id = node_map.get(paper_key)

        if not paper_id:
            continue

        normalized_concepts = {
            normalize_concept_name(concept)
            for concept in article.get("concepts", [])
            if concept
        }

        paper_concepts[paper_id] = normalized_concepts

    paper_ids = list(paper_concepts.keys())

    for i in range(len(paper_ids)):
        for j in range(i + 1, len(paper_ids)):
            paper_id_1 = paper_ids[i]
            paper_id_2 = paper_ids[j]

            shared_concepts = paper_concepts[paper_id_1].intersection(paper_concepts[paper_id_2])

            if len(shared_concepts) >= 2:
                learn_edge(network_id, paper_id_1, paper_id_2, "related_to")
                print(
                    f"Linked similar papers: {paper_id_1} -> {paper_id_2} "
                    f"(shared concepts: {sorted(shared_concepts)})"
                )


# Main execution logic 
# depends on changes in .env for configuration of the PubMed query, 
# target network, and reingestion mode

def main() -> None:
    print(f"PubMed query: {PUBMED_QUERY}")
    print(f"Target network name: {NETWORK_NAME}")

    network_id = get_or_create_network_id(NETWORK_NAME)
    pmids = search_pubmed(PUBMED_QUERY, PUBMED_MAX_RECORDS)
    if not pmids:
        print("No PubMed results found.")
        return

    print(f"Found PMIDs: {pmids}")

    if PUBMED_REINGEST_MODE not in {"new_only", "force_all"}:
        raise ValueError(
            f"Invalid PUBMED_REINGEST_MODE: {PUBMED_REINGEST_MODE}. "
            f"Use 'new_only' or 'force_all'."
        )

    seen_pmids = get_seen_pmids(NETWORK_NAME, PUBMED_QUERY)

    # Determine which PMIDs to ingest based on reingest mode and previously seen PMIDs for this network/query
    if PUBMED_REINGEST_MODE == "force_all":
        selected_pmids = pmids
        print("Reingest mode: force_all")
        print(f"PMIDs selected for ingestion: {selected_pmids}")
    else:
        selected_pmids = [pmid for pmid in pmids if pmid not in seen_pmids]
        print("Reingest mode: new_only")
        print(f"New PMIDs to ingest: {selected_pmids}")

        if not selected_pmids:
            print("No new PMIDs to ingest. All fetched papers were already processed for this network/query.")
            return

    # Fetch details for selected PMIDs, parse them, and ingest into the graph
    xml_text = fetch_pubmed_details(selected_pmids)
    articles = parse_pubmed_xml(xml_text)

    if not articles:
        print("No PubMed article details could be parsed.")
        return

    node_map = get_existing_nodes(network_id)

    for article in articles:
        print()
        print(f"Ingesting article: {article['title']}")
        if article.get("text_concepts"):
            print(f"Extracted text concepts: {article['text_concepts']}")
        ingest_article(network_id, node_map, article)
        
    print()
    print("Linking similar papers...")
    link_similar_papers(network_id, node_map, articles)
    ingested_pmids = [article["pmid"] for article in articles if article.get("pmid")]
    add_seen_pmids(NETWORK_NAME, PUBMED_QUERY, ingested_pmids)

    print(f"Saved {len(ingested_pmids)} ingested PMIDs to state for this network/query.")

    print()
    print("PubMed ingestion complete.")


if __name__ == "__main__":
    main()