"""Wrapper for interacting with Rust engine via subprocess."""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from aureus.tools.schemas import (
    BacktestSpec,
    BacktestToolInput,
    CRVVerifyToolInput,
    HipcortexCommitInput,
    HipcortexSearchInput,
    ToolCall,
    ToolResult,
    ToolType,
)


class RustEngineWrapper:
    """Wrapper for executing Rust engine commands via subprocess."""
    
    def __init__(
        self,
        rust_cli_path: Optional[Path] = None,
        hipcortex_cli_path: Optional[Path] = None,
    ):
        """Initialize Rust engine wrapper.
        
        Args:
            rust_cli_path: Path to quant_engine binary (default: auto-detect)
            hipcortex_cli_path: Path to hipcortex binary (default: auto-detect)
        """
        self.rust_cli_path = rust_cli_path or self._find_rust_cli()
        self.hipcortex_cli_path = hipcortex_cli_path or self._find_hipcortex_cli()
        
    def _find_rust_cli(self) -> Path:
        """Find the Rust CLI binary."""
        # Try release build first, then debug
        repo_root = Path(__file__).parent.parent.parent.parent
        release_path = repo_root / "target" / "release" / "quant_engine"
        debug_path = repo_root / "target" / "debug" / "quant_engine"
        
        if release_path.exists():
            return release_path
        elif debug_path.exists():
            return debug_path
        else:
            raise RuntimeError(
                "Rust CLI binary not found. Please build with 'cargo build --release'"
            )
    
    def _find_hipcortex_cli(self) -> Path:
        """Find the hipcortex CLI binary."""
        repo_root = Path(__file__).parent.parent.parent.parent
        release_path = repo_root / "target" / "release" / "hipcortex"
        debug_path = repo_root / "target" / "debug" / "hipcortex"
        
        if release_path.exists():
            return release_path
        elif debug_path.exists():
            return debug_path
        else:
            raise RuntimeError(
                "Hipcortex CLI binary not found. Please build with 'cargo build --release'"
            )
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call.
        
        Args:
            tool_call: The tool call to execute
            
        Returns:
            ToolResult with execution results
        """
        try:
            if tool_call.tool_type == ToolType.BACKTEST:
                return self._run_backtest(tool_call.parameters)
            elif tool_call.tool_type == ToolType.CRV_VERIFY:
                return self._run_crv_verify(tool_call.parameters)
            elif tool_call.tool_type == ToolType.HIPCORTEX_COMMIT:
                return self._run_hipcortex_commit(tool_call.parameters)
            elif tool_call.tool_type == ToolType.HIPCORTEX_SEARCH:
                return self._run_hipcortex_search(tool_call.parameters)
            elif tool_call.tool_type == ToolType.HIPCORTEX_SHOW:
                return self._run_hipcortex_show(tool_call.parameters)
            elif tool_call.tool_type == ToolType.RUN_TESTS:
                return self._run_tests(tool_call.parameters)
            elif tool_call.tool_type == ToolType.CHECK_DETERMINISM:
                return self._check_determinism(tool_call.parameters)
            elif tool_call.tool_type == ToolType.LINT:
                return self._run_lint(tool_call.parameters)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown tool type: {tool_call.tool_type}",
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_backtest(self, params: BacktestToolInput) -> ToolResult:
        """Run a backtest using the Rust engine."""
        # Create temporary spec file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as spec_file:
            json.dump(params.spec.model_dump(), spec_file)
            spec_path = spec_file.name
        
        try:
            # Create output directory
            os.makedirs(params.output_dir, exist_ok=True)
            
            # Run backtest
            cmd = [
                str(self.rust_cli_path),
                "backtest",
                "--spec", spec_path,
                "--data", params.data_path,
                "--out", params.output_dir,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Backtest failed: {result.stderr}",
                )
            
            # Read results
            stats_path = Path(params.output_dir) / "stats.json"
            crv_path = Path(params.output_dir) / "crv_report.json"
            
            output = {"stdout": result.stdout}
            
            if stats_path.exists():
                with open(stats_path) as f:
                    output["stats"] = json.load(f)
            
            if crv_path.exists():
                with open(crv_path) as f:
                    output["crv_report"] = json.load(f)
            
            return ToolResult(success=True, output=output)
        
        finally:
            # Clean up temp file
            os.unlink(spec_path)
    
    def _run_crv_verify(self, params: CRVVerifyToolInput) -> ToolResult:
        """Run CRV verification (already part of backtest)."""
        # CRV is automatically run as part of backtest
        # This is a no-op that just reads existing CRV report
        try:
            # Find CRV report in the same directory as stats
            stats_dir = Path(params.stats_path).parent
            crv_path = stats_dir / "crv_report.json"
            
            if not crv_path.exists():
                return ToolResult(
                    success=False,
                    error="CRV report not found. Run backtest first.",
                )
            
            with open(crv_path) as f:
                crv_report = json.load(f)
            
            return ToolResult(
                success=crv_report.get("passed", False),
                output={"crv_report": crv_report},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_hipcortex_commit(self, params: HipcortexCommitInput) -> ToolResult:
        """Commit an artifact to hipcortex."""
        try:
            cmd = [
                str(self.hipcortex_cli_path),
                "commit",
                "--artifact", params.artifact_path,
                "--message", params.message,
            ]
            
            if params.goal:
                cmd.extend(["--goal", params.goal])
            
            if params.regime_tags:
                for tag in params.regime_tags:
                    cmd.extend(["--tag", tag])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Hipcortex commit failed: {result.stderr}",
                )
            
            # Extract artifact ID from output
            artifact_id = None
            for line in result.stdout.split("\n"):
                if "Committed" in line or "hash" in line.lower():
                    # Parse hash from output
                    parts = line.split()
                    for part in parts:
                        if len(part) == 64:  # SHA-256 hash
                            artifact_id = part
                            break
            
            return ToolResult(
                success=True,
                output={"stdout": result.stdout},
                artifact_id=artifact_id,
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_hipcortex_search(self, params: HipcortexSearchInput) -> ToolResult:
        """Search for artifacts in hipcortex."""
        try:
            cmd = [str(self.hipcortex_cli_path), "search"]
            
            if params.goal:
                cmd.extend(["--goal", params.goal])
            
            if params.tag:
                cmd.extend(["--tag", params.tag])
            
            cmd.extend(["--limit", str(params.limit)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Hipcortex search failed: {result.stderr}",
                )
            
            return ToolResult(
                success=True,
                output={"stdout": result.stdout, "results": result.stdout},
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_hipcortex_show(self, params: Dict[str, Any]) -> ToolResult:
        """Show artifact details from hipcortex."""
        try:
            artifact_id = params.get("artifact_id")
            if not artifact_id:
                return ToolResult(success=False, error="artifact_id required")
            
            cmd = [str(self.hipcortex_cli_path), "show", artifact_id]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Hipcortex show failed: {result.stderr}",
                )
            
            return ToolResult(
                success=True,
                output={"stdout": result.stdout},
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_tests(self, params: Dict[str, Any]) -> ToolResult:
        """Run Rust tests."""
        try:
            repo_root = Path(__file__).parent.parent.parent.parent
            
            cmd = ["cargo", "test", "--all"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=repo_root,
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _check_determinism(self, params: Dict[str, Any]) -> ToolResult:
        """Check determinism by running backtest multiple times."""
        try:
            spec_path = params.get("spec_path")
            data_path = params.get("data_path")
            runs = params.get("runs", 3)
            
            if not spec_path or not data_path:
                return ToolResult(
                    success=False,
                    error="spec_path and data_path required",
                )
            
            # Run backtest multiple times and compare hashes
            hashes = []
            for i in range(runs):
                with tempfile.TemporaryDirectory() as tmpdir:
                    cmd = [
                        str(self.rust_cli_path),
                        "backtest",
                        "--spec", spec_path,
                        "--data", data_path,
                        "--out", tmpdir,
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, check=False)
                    
                    if result.returncode != 0:
                        return ToolResult(
                            success=False,
                            error=f"Run {i+1} failed: {result.stderr.decode()}",
                        )
                    
                    # Read stats and compute hash
                    stats_path = Path(tmpdir) / "stats.json"
                    with open(stats_path) as f:
                        stats_content = f.read()
                    
                    hash_val = hashlib.sha256(stats_content.encode()).hexdigest()
                    hashes.append(hash_val)
            
            # Check if all hashes are the same
            is_deterministic = len(set(hashes)) == 1
            
            return ToolResult(
                success=is_deterministic,
                output={
                    "deterministic": is_deterministic,
                    "runs": runs,
                    "hashes": hashes,
                },
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_lint(self, params: Dict[str, Any]) -> ToolResult:
        """Run cargo clippy for linting."""
        try:
            repo_root = Path(__file__).parent.parent.parent.parent
            
            cmd = ["cargo", "clippy", "--all", "--", "-D", "warnings"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=repo_root,
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
            )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
