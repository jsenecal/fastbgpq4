import asyncio
import json
from typing import Any

from app.exceptions import BGPq4ExecutionError, BGPq4ParseError, BGPq4TimeoutError


class BGPq4Client:
    """Client for executing bgpq4 commands."""

    def __init__(
        self,
        binary_path: str,
        default_sources: list[str],
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        self.binary_path = binary_path
        self.default_sources = default_sources
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def _build_command(
        self,
        target: str,
        sources: list[str] | None,
        format: str,
        aggregate: bool = False,
        min_masklen: int | None = None,
        max_masklen: int | None = None,
    ) -> list[str]:
        """Build bgpq4 command."""
        cmd = [self.binary_path]

        # JSON output flag
        if format == "json":
            cmd.append("-j")

        # Sources
        sources_list = sources if sources else self.default_sources
        cmd.extend(["-S", ",".join(sources_list)])

        # Aggregation
        if aggregate:
            cmd.append("-A")

        # Masklen filtering
        if min_masklen is not None:
            cmd.extend(["-r", str(min_masklen)])
        if max_masklen is not None:
            cmd.extend(["-R", str(max_masklen)])

        # Target
        cmd.append(target)

        return cmd

    async def execute(
        self,
        target: str,
        sources: list[str] | None,
        format: str,
        aggregate: bool = False,
        min_masklen: int | None = None,
        max_masklen: int | None = None,
        timeout_seconds: float = 30.0,
    ) -> str:
        """Execute bgpq4 command and return raw output."""
        cmd = self._build_command(
            target=target,
            sources=sources,
            format=format,
            aggregate=aggregate,
            min_masklen=min_masklen,
            max_masklen=max_masklen,
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

            if process.returncode != 0:
                raise BGPq4ExecutionError(
                    message=f"bgpq4 failed with return code {process.returncode}",
                    return_code=process.returncode,
                    stderr=stderr.decode(),
                )

            return stdout.decode()

        except TimeoutError:
            raise BGPq4TimeoutError(
                message=f"bgpq4 execution timed out after {timeout_seconds}s",
                timeout_seconds=timeout_seconds,
            )

    def parse_json_output(self, raw_output: str) -> dict[str, Any]:
        """Parse bgpq4 JSON output into standardized format."""
        try:
            data = json.loads(raw_output)
            # bgpq4 JSON format: {"NN": [{"prefix": "..."}, ...]}
            prefixes = []
            if "NN" in data:
                prefixes = [entry.get("prefix") for entry in data["NN"]]

            return {"prefixes": prefixes, "count": len(prefixes)}
        except json.JSONDecodeError as e:
            raise BGPq4ParseError(
                message=f"Failed to parse bgpq4 JSON output: {e}", output=raw_output
            )

    async def execute_with_retry(
        self,
        target: str,
        sources: list[str] | None,
        format: str,
        aggregate: bool = False,
        min_masklen: int | None = None,
        max_masklen: int | None = None,
        timeout_seconds: float = 30.0,
    ) -> str:
        """Execute bgpq4 with retry logic for transient failures."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await self.execute(
                    target=target,
                    sources=sources,
                    format=format,
                    aggregate=aggregate,
                    min_masklen=min_masklen,
                    max_masklen=max_masklen,
                    timeout_seconds=timeout_seconds,
                )
            except (BGPq4ExecutionError, BGPq4TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                raise

        # Should not reach here, but for type safety
        if last_error:
            raise last_error
