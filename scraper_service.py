# scraper_service.py
"""
Background scraper service that receives selectors from GUI
"""

import socket
import json
import threading
import time
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Your existing scraper imports
from scraper.searcher import search_and_fetch
from utils.logger import setup_logger


class ScraperService:
    """Background scraper service"""

    def __init__(self, port=8765):
        self.port = port
        self.running = False
        self.logger = setup_logger("ScraperService", log_file="scraper_service.log")
        self.current_job = None

        # Create data directory
        Path("data_exports").mkdir(exist_ok=True)

    def start_service(self):
        """Start the scraper service"""
        self.running = True
        self.logger.info(f"🚀 Scraper Service starting on port {self.port}")

        # Start socket server
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()

        print(f"🚀 Scraper Service running on port {self.port}")
        print("✅ Ready to receive commands from GUI")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_service()

    def _run_server(self):
        """Run the socket server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind(('localhost', self.port))
            server_socket.listen(5)

            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    self.logger.info(f"📡 Connection from {address}")

                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Socket error: {e}")

        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            server_socket.close()

    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            # Receive data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk

                # Check if we have complete JSON
                try:
                    json.loads(data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue

            if data:
                command = json.loads(data.decode('utf-8'))
                response = self._process_command(command)

                # Send response
                response_data = json.dumps(response).encode('utf-8')
                client_socket.send(response_data)

        except Exception as e:
            self.logger.error(f"Client handling error: {e}")
            error_response = json.dumps({
                "status": "error",
                "message": str(e)
            })
            client_socket.send(error_response.encode('utf-8'))
        finally:
            client_socket.close()

    def _process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from GUI"""
        cmd_type = command.get("type")

        if cmd_type == "ping":
            return {"status": "ok", "message": "Scraper service is running"}

        elif cmd_type == "start_scraping":
            return self._start_scraping_job(command)

        elif cmd_type == "get_status":
            return self._get_job_status()

        elif cmd_type == "stop_job":
            return self._stop_current_job()

        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def _start_scraping_job(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Start a scraping job"""
        if self.current_job and self.current_job.get("running"):
            return {
                "status": "error",
                "message": "Another job is already running"
            }

        try:
            job_id = f"job_{int(time.time())}"
            selectors = command.get("selectors", [])
            target_urls = command.get("target_urls", [])
            project_name = command.get("project_name", "gui_project")

            self.logger.info(f"🎯 Starting scraping job: {job_id}")
            self.logger.info(f"📋 Selectors: {len(selectors)}")
            self.logger.info(f"🌐 Target URLs: {len(target_urls)}")

            # Create job entry
            self.current_job = {
                "id": job_id,
                "running": True,
                "started_at": datetime.now().isoformat(),
                "selectors": selectors,
                "target_urls": target_urls,
                "project_name": project_name,
                "progress": 0,
                "status": "starting"
            }

            # Start scraping in background thread
            scraping_thread = threading.Thread(
                target=self._run_scraping_job,
                args=(job_id, selectors, target_urls, project_name),
                daemon=True
            )
            scraping_thread.start()

            return {
                "status": "started",
                "job_id": job_id,
                "message": f"Scraping job {job_id} started"
            }

        except Exception as e:
            self.logger.error(f"Failed to start job: {e}")
            return {"status": "error", "message": str(e)}

    def _run_scraping_job(self, job_id: str, selectors: List[Dict], target_urls: List[str], project_name: str):
        """Run the actual scraping job"""
        try:
            self.current_job["status"] = "generating_config"
            self.current_job["progress"] = 10

            # Generate YAML config from selectors
            config_data = self._generate_config_from_selectors(
                selectors, target_urls, project_name
            )

            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
                temp_config_path = f.name

            self.current_job["status"] = "scraping"
            self.current_job["progress"] = 20

            # Progress callback
            def progress_callback(message, percentage):
                if self.current_job:
                    gui_progress = 20 + int(percentage * 0.7)  # Scale to 20-90%
                    self.current_job["progress"] = gui_progress
                    self.current_job["current_message"] = message
                    self.logger.info(f"📊 {job_id}: {message} ({gui_progress}%)")

            # Run the scraper
            enriched_items = search_and_fetch(
                query_or_config_path=temp_config_path,
                logger=self.logger,
                progress_callback=progress_callback
            )

            # Job completed
            self.current_job["status"] = "completed"
            self.current_job["progress"] = 100
            self.current_job["running"] = False
            self.current_job["completed_at"] = datetime.now().isoformat()
            self.current_job["items_scraped"] = len(enriched_items)

            self.logger.info(f"✅ Job {job_id} completed: {len(enriched_items)} items")

            # Cleanup
            Path(temp_config_path).unlink()

        except Exception as e:
            self.logger.error(f"Job {job_id} failed: {e}")
            if self.current_job:
                self.current_job["status"] = "failed"
                self.current_job["error"] = str(e)
                self.current_job["running"] = False

    def _generate_config_from_selectors(self, selectors: List[Dict], target_urls: List[str], project_name: str) -> Dict:
        """Generate YAML config from GUI selectors"""
        return {
            "domain_info": {
                "name": project_name,
                "description": f"Live scraping job from GUI",
                "domain": "gui_generated"
            },
            "global_user_agent": "RAGScraper-Live",
            "sources": [{
                "name": project_name.lower().replace(' ', '_'),
                "seeds": target_urls,
                "source_type": "gui_generated",
                "selectors": {
                    "custom_fields": [
                        {
                            "name": sel.get("name", f"field_{i}"),
                            "selector": sel.get("selector", ""),
                            "extract_type": sel.get("extraction_type", "text"),
                            "attribute_name": sel.get("attribute_name"),
                            "is_list": sel.get("is_list", False),
                            "semantic_label": sel.get("semantic_label", "content"),
                            "rag_importance": sel.get("rag_importance", "medium"),
                            "required": sel.get("required", False)
                        }
                        for i, sel in enumerate(selectors)
                    ]
                },
                "crawl": {
                    "depth": 1,
                    "delay_seconds": 2.0,
                    "respect_robots_txt": True
                },
                "export": {
                    "format": "jsonl",
                    "output_path": f"./data_exports/{project_name.lower().replace(' ', '_')}/live_scrape.jsonl"
                }
            }]
        }

    def _get_job_status(self) -> Dict[str, Any]:
        """Get current job status"""
        if not self.current_job:
            return {
                "status": "no_job",
                "message": "No active job"
            }

        return {
            "status": "ok",
            "job": {
                "id": self.current_job["id"],
                "running": self.current_job["running"],
                "status": self.current_job["status"],
                "progress": self.current_job["progress"],
                "current_message": self.current_job.get("current_message", ""),
                "items_scraped": self.current_job.get("items_scraped", 0)
            }
        }

    def _stop_current_job(self) -> Dict[str, Any]:
        """Stop current job"""
        if self.current_job and self.current_job["running"]:
            self.current_job["running"] = False
            self.current_job["status"] = "stopped"
            return {"status": "ok", "message": "Job stopped"}
        else:
            return {"status": "error", "message": "No running job to stop"}

    def stop_service(self):
        """Stop the service"""
        self.running = False
        self.logger.info("🛑 Scraper Service stopping")
        print("🛑 Scraper Service stopped")


class ScraperClient:
    """Client to communicate with the scraper service from GUI"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port

    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to scraper service"""
        try:
            # Create socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)  # 30 second timeout

            # Connect
            client_socket.connect((self.host, self.port))

            # Send command
            command_data = json.dumps(command).encode('utf-8')
            client_socket.send(command_data)

            # Receive response
            response_data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk

                # Try to parse JSON
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue

            client_socket.close()
            return response

        except Exception as e:
            return {
                "status": "error",
                "message": f"Communication error: {str(e)}"
            }

    def ping(self) -> bool:
        """Check if scraper service is running"""
        response = self.send_command({"type": "ping"})
        return response.get("status") == "ok"

    def start_scraping(self, selectors: List[Dict], target_urls: List[str], project_name: str) -> Dict[str, Any]:
        """Start scraping job"""
        return self.send_command({
            "type": "start_scraping",
            "selectors": selectors,
            "target_urls": target_urls,
            "project_name": project_name
        })

    def get_status(self) -> Dict[str, Any]:
        """Get job status"""
        return self.send_command({"type": "get_status"})

    def stop_job(self) -> Dict[str, Any]:
        """Stop current job"""
        return self.send_command({"type": "stop_job"})


# Main entry point for running as service
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--service":
        # Run as service
        service = ScraperService()
        service.start_service()
    else:
        # Show usage
        print("🚀 Scraper Service")
        print("==================")
        print()
        print("Usage:")
        print("  python scraper_service.py --service    # Run scraper service")
        print()
        print("The service will listen on port 8765 for commands from the GUI")