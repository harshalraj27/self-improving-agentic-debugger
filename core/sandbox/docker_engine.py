from __future__ import annotations

import time
from pathlib import Path
from typing import Final, Tuple
import requests
import docker
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from requests.exceptions import ReadTimeout, ConnectionError

from core.runners.base import ExecutionResult


class DockerSandboxWrapper:
    IMAGE_NAME: Final[str] = "agentic-sandbox:latest"
    CONTAINER_WORKDIR: Final[str] = "/app"
    _TIMEOUT_EXIT_CODE: Final[int] = 124

    def __init__(self) -> None:
        self.client: docker.DockerClient = docker.from_env()

    def run_in_container(
        self,
        host_file_path: str,
        command: list[str],
        timeout: int = 5,
    ) -> tuple[int, str, str, float]:
        resolved_file = Path(host_file_path).resolve()
        host_mount = str(resolved_file.parent)
        volumes: dict[str, dict[str, str]] = {
            host_mount: {"bind": self.CONTAINER_WORKDIR, "mode": "ro"},
        }

        container: Container | None = None
        start = time.perf_counter()
        exit_code = 1
        stdout = ""
        stderr = ""

        try:
            container = self.client.containers.run(
                self.IMAGE_NAME,
                command=command,
                detach=True,
                volumes=volumes,
                working_dir=self.CONTAINER_WORKDIR,
                network_disabled=True,
                mem_limit="128m",
            )
            wait_result = container.wait(timeout=timeout)
            exit_code = int(wait_result.get("StatusCode", 1))
            stdout = self._decode_logs(container, stdout=True, stderr=False)
            stderr = self._decode_logs(container, stdout=False, stderr=True)
        except (ReadTimeout, ConnectionError, APIError):
            exit_code = self._TIMEOUT_EXIT_CODE
            if container is not None:
                try:
                    stdout = self._decode_logs(container, stdout=True, stderr=False)
                    stderr = self._decode_logs(container, stdout=False, stderr=True)
                except Exception:
                    pass
                self._kill_container(container)
            if not stderr.strip():
                stderr = f"Execution exceeded timeout of {timeout}s"
        finally:
            self._remove_container(container)

        runtime_ms = (time.perf_counter() - start) * 1000.0
        return exit_code, stdout, stderr, runtime_ms

    @staticmethod
    def _decode_logs(
        container: Container,
        *,
        stdout: bool,
        stderr: bool,
    ) -> str:
        return container.logs(stdout=stdout, stderr=stderr).decode(
            "utf-8", errors="replace"
        )

    @staticmethod
    def _kill_container(container: Container) -> None:
        try:
            container.kill()
        except APIError:
            pass

    @staticmethod
    def _remove_container(container: Container | None) -> None:
        if container is None:
            return
        try:
            container.remove(force=True)
        except (NotFound, APIError):
            pass