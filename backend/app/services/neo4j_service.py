import logging
from typing import List, Dict, Any, Tuple
from neo4j import GraphDatabase, AsyncGraphDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        self.driver = None
        self.is_connected = False
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            self.is_connected = True
        except Exception as e:
            logger.warning(f"Could not connect to Neo4j database. Graph features will use in-memory mock. Error: {e}")
            self.mock_nodes = {}
            self.mock_rels = []

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def create_node(self, label: str, name: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Creates a node in Neo4j. Label can be Concept, Technology, Paper, Author, Organization.
        """
        properties = properties or {}
        properties["name"] = name
        
        # Sanitize label to prevent injection
        label = str(label).replace("`", "").strip() or "Concept"
        
        if not self.is_connected:
            node_key = f"{label}:{name}"
            self.mock_nodes[node_key] = {"label": label, "name": name, "properties": properties}
            return properties

        query = f"""
        MERGE (n:`{label}` {{name: $name}})
        SET n += $properties
        RETURN n
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=name, properties=properties)
            record = await result.single()
            return dict(record["n"]) if record else properties

    async def create_relationship(
        self, 
        source_label: str, source_name: str,
        target_label: str, target_name: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ):
        """
        Creates a directed relationship between two nodes.
        rel_type can be RELATED_TO, USES, IMPROVES, CAUSES, REFERENCES, etc.
        """
        properties = properties or {}
        
        # Sanitize types to prevent injection
        source_label = str(source_label).replace("`", "").strip() or "Concept"
        target_label = str(target_label).replace("`", "").strip() or "Concept"
        rel_type = str(rel_type).replace("`", "").strip() or "RELATED_TO"
        
        if not self.is_connected:
            rel = {
                "source_label": source_label, "source_name": source_name,
                "target_label": target_label, "target_name": target_name,
                "rel_type": rel_type, "properties": properties
            }
            self.mock_rels.append(rel)
            return

        query = f"""
        MATCH (a:`{source_label}` {{name: $source_name}})
        MATCH (b:`{target_label}` {{name: $target_name}})
        MERGE (a)-[r:`{rel_type}`]->(b)
        SET r += $properties
        RETURN r
        """
        async with self.driver.session() as session:
            await session.run(
                query, 
                source_name=source_name, 
                target_name=target_name, 
                properties=properties
            )

    async def get_graph_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns all nodes and links for visualization.
        """
        if not self.is_connected:
            nodes = []
            for k, val in self.mock_nodes.items():
                nodes.append({"id": val["name"], "label": val["label"], "properties": val["properties"]})
            links = []
            for r in self.mock_rels:
                links.append({
                    "source": r["source_name"],
                    "target": r["target_name"],
                    "type": r["rel_type"],
                    "properties": r["properties"]
                })
            return {"nodes": nodes, "links": links}

        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT 500
        """
        nodes_map = {}
        links = []

        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                n = record["n"]
                if n:
                    labels = list(n.labels)
                    label = labels[0] if labels else "Concept"
                    nodes_map[n["name"]] = {
                        "id": n["name"],
                        "label": label,
                        "properties": dict(n)
                    }

                m = record["m"]
                r = record["r"]
                if m and r:
                    m_labels = list(m.labels)
                    m_label = m_labels[0] if m_labels else "Concept"
                    nodes_map[m["name"]] = {
                        "id": m["name"],
                        "label": m_label,
                        "properties": dict(m)
                    }
                    links.append({
                        "source": n["name"],
                        "target": m["name"],
                        "type": r.type,
                        "properties": dict(r)
                    })

        return {"nodes": list(nodes_map.values()), "links": links}

    async def find_connecting_paths(self, source: str, target: str) -> List[Dict[str, Any]]:
        """
        Multi-hop path discovery between two nodes (Module 10).
        """
        if not self.is_connected:
            # Simple mock path matching
            paths = []
            for r in self.mock_rels:
                if (r["source_name"].lower() == source.lower() and r["target_name"].lower() == target.lower()) or \
                   (r["source_name"].lower() == target.lower() and r["target_name"].lower() == source.lower()):
                    paths.append({
                        "path": [r["source_name"], r["rel_type"], r["target_name"]]
                    })
            return paths

        query = """
        MATCH p = shortestPath((a {name: $source})-[*..5]-(b {name: $target}))
        RETURN p
        """
        paths = []
        async with self.driver.session() as session:
            result = await session.run(query, source=source, target=target)
            async for record in result:
                p = record["p"]
                nodes = [n["name"] for n in p.nodes]
                rels = [r.type for r in p.relationships]
                
                # Combine nodes and relations in sequence
                path_seq = []
                for i in range(len(rels)):
                    path_seq.append(nodes[i])
                    path_seq.append(rels[i])
                path_seq.append(nodes[-1])
                
                paths.append({
                    "nodes": nodes,
                    "relationships": rels,
                    "path_sequence": path_seq
                })
        return paths

    async def detect_research_gaps(self) -> List[Dict[str, Any]]:
        """
        Module 11: Identify sparse nodes, weak connections, or structural holes.
        """
        if not self.is_connected:
            # Mock gaps
            return [
                {
                    "concept": "AI and Healthcare Integration",
                    "reason": "Sparse relationships in the current knowledge sphere.",
                    "suggestions": ["Explore causal links between deep neural nets and patient diagnosis databases."]
                },
                {
                    "concept": "Quantum Computing Applications",
                    "reason": "Isolated node with no external connections.",
                    "suggestions": ["Investigate dependencies on cryptography algorithms or optimization methods."]
                }
            ]

        # Query for nodes with degree centrality of 1 or 0 (sparse nodes)
        query = """
        MATCH (n)
        WITH n, count{(n)--()} as degree
        WHERE degree <= 1
        RETURN n.name as concept, labels(n)[0] as type, degree
        ORDER BY degree ASC
        LIMIT 10
        """
        gaps = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                concept = record["concept"]
                ctype = record["type"]
                degree = record["degree"]
                
                gaps.append({
                    "concept": concept,
                    "type": ctype,
                    "reason": f"Sparse node detected with only {degree} connections.",
                    "suggestions": [
                        f"Perform literature reviews relating {concept} to top trending research items.",
                        f"Investigate downstream impacts and causal links involving {concept}."
                    ]
                })
        return gaps

    async def get_analytics(self) -> Dict[str, Any]:
        """
        Module 16: Return analytics data like total nodes, edges, top labels.
        """
        if not self.is_connected:
            labels_cnt = {}
            for n in self.mock_nodes.values():
                labels_cnt[n["label"]] = labels_cnt.get(n["label"], 0) + 1
            return {
                "total_nodes": len(self.mock_nodes),
                "total_relationships": len(self.mock_rels),
                "node_types": labels_cnt
            }

        async with self.driver.session() as session:
            nodes_res = await session.run("MATCH (n) RETURN count(n) as count")
            nodes_count = (await nodes_res.single())["count"]

            rels_res = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rels_count = (await rels_res.single())["count"]

            types_res = await session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            node_types = {}
            async for r in types_res:
                if r["label"]:
                    node_types[r["label"]] = r["count"]

            return {
                "total_nodes": nodes_count,
                "total_relationships": rels_count,
                "node_types": node_types
            }

    async def clear_graph(self):
        if not self.is_connected:
            self.mock_nodes.clear()
            self.mock_rels.clear()
            return
        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

neo4j_service = Neo4jService()
