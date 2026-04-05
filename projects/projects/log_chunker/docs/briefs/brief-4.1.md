# Implementation Brief: Task 4.1 - Plugin Interface

**Goal**: To expand the `BaseChunkingPlugin` interface to allow plugins to contribute rich, structured data to the `IntelligenceReport`.

**Inputs**: N/A (Modifying a class definition).

**Outputs**: An updated `plugins/base.py` file.

**Pseudocode / Action Plan**:

1.  **Modify `plugins/base.py`**.
2.  Add a new method to the `BaseChunkingPlugin` abstract base class:
    ```python
    @abstractmethod
    def analyze_chunks(self, chunks: List[Tuple[str, ChunkInfo]]) -> Dict[str, Any]:
        """Perform a detailed analysis on the generated chunks.

        Returns:
            A dictionary containing structured analysis data.
            The keys of this dictionary should be unique to the plugin.
        """
        return {}
    ```
3.  **Update `PluginManager`**: In `plugin_manager.py`, create a new method `run_analysis_plugins`. This method will iterate through all active plugins, call their `analyze_chunks` method, and merge the resulting dictionaries into a single analysis dictionary.
4.  **Engine Integration**: The `IntelligenceEngine` will call `plugin_manager.run_analysis_plugins` and attach the result to a new field in the `IntelligenceReport` called `plugin_analysis_results`.

**Key Considerations**:
- This is a significant change to the plugin contract. All existing plugins will need to be updated to implement the new method (even if it just returns an empty dictionary).
- The keys in the returned dictionary must be namespaced (e.g., `"security_plugin": {"vulnerabilities": [...]}`) to avoid conflicts between plugins.
