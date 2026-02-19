# Engineering Spec: Constellate Labs

## 1. Overview

### 1.1 Purpose
Constellate Labs is an open-source text-to-drone flight map software that converts natural language descriptions into SkyBrush Studio-compliant drone light show flight paths. Users describe objects or patterns in text (e.g., "a green dragon"), and the system generates executable flight code compatible with SkyBrush Studio.

### 1.2 Goals
* **Quality**: Generate flight paths that respect physical constraints and safety requirements
* **Compatibility**: Output SkyBrush Studio-compatible flight code
* **Determinism**: Ensure reproducible results for the same input

### 1.3 Scope
This specification covers the complete pipeline from natural language input to SkyBrush Studio export, including all intermediate processing steps.

---

## 2. System Architecture

### 2.1 Pipeline Overview
The system implements a multi-stage pipeline:


1. Natural language prompt to LLM generates an SVG
Convert text to structured vector graphics
    * <ins>Responsibility</ins>: Convert text to structured vector graphics 
2.  Deterministic geometry processing
    * <ins>Responsibility</ins>: Normalize and optimize geometric representation
3. Poisson disk sampling
    * <ins>Responsibility</ins>: Generate spatially-distributed waypoint positions
4. Physical constraint enforcement
    * <ins>Responsibility</ins>: Validate and adjust for drone physics and safety
5. SkyBrush Studio API call to generate (.skyc) file
    * <ins>Responsibility</ins>: Format output for SkyBrush Studio import

---

## 3. Pipeline Stages

### 3.1 Stage 1: LLM-Generated SVG

#### 3.1.1 Purpose
Convert natural language descriptions into structured SVG (Scalable Vector Graphics) representations that capture the intended visual pattern.

#### 3.1.2 Input
- **Natural language prompt** (string): User description of desired pattern/object
  - Example: `"a green dragon"`, `"spiral pattern"`, `"heart shape"`
- **Optional parameters**:
  - Canvas dimensions (default: configurable)
  - Style preferences (colors, complexity level)

#### 3.1.3 Process
1. **Prompt Engineering**: Format user input with SVG generation instructions
2. **LLM Inference**: Call language model API (e.g., GPT-4, Claude) with structured prompt
3. **SVG Extraction**: Parse LLM response to extract valid SVG markup
4. **Validation**: Verify SVG syntax and structure

#### 3.1.4 Output
- **SVG Document** (XML string): Valid SVG containing paths, shapes, and styling
- **Metadata**: Generation parameters, timestamp, prompt used

#### 3.1.5 Technical Requirements
- LLM API integration (OpenAI, Anthropic, or local model)
- SVG parsing/validation library
- Error handling for malformed LLM responses
- Retry logic for API failures

#### 3.1.6 Constraints
- SVG must be 2D (no 3D transformations)
- Paths should be closed or explicitly marked as open
- Maximum complexity limits to prevent excessive detail

---

### 3.2 Stage 2: Deterministic Geometry Processing

#### 3.2.1 Purpose
Normalize, clean, and optimize the SVG geometry to prepare for waypoint generation. Ensure geometric consistency and remove artifacts.

#### 3.2.2 Input
- SVG document from Stage 1
- Processing parameters (simplification tolerance, coordinate system)

#### 3.2.3 Process
1. **SVG Parsing**: Extract geometric primitives (paths, shapes, groups)
2. **Coordinate Normalization**: Convert to consistent coordinate system (e.g., meters, origin-centered)
3. **Path Flattening**: Convert Bézier curves to polyline approximations
4. **Simplification**: Reduce vertex count while preserving shape (Douglas-Peucker algorithm)
5. **Topology Validation**: Ensure paths are valid, non-self-intersecting where required
6. **Bounding Box Calculation**: Determine spatial extent

#### 3.2.4 Output
- **Processed Geometry**: Normalized 2D paths as arrays of (x, y) coordinates
- **Metadata**: Bounding box, path count, total path length, coordinate system info

#### 3.2.5 Technical Requirements
- SVG parsing library (e.g., `svgpathtools`, `cairosvg`)
- Geometric algorithms (path simplification, intersection detection)
- Coordinate transformation utilities
- NumPy for efficient array operations

#### 3.2.6 Constraints
- All coordinates must be finite and within reasonable bounds
- Paths must maintain topological consistency
- Maximum path length limits to prevent memory issues

---

### 3.3 Stage 3: Poisson Disk Sampling

#### 3.3.1 Purpose
Generate spatially-distributed waypoint positions along the processed paths using Poisson disk sampling to ensure uniform spacing and visual quality.

#### 3.3.2 Input
- Processed geometry paths from Stage 2
- Sampling parameters:
  - Minimum distance between waypoints (radius)
  - Maximum attempts per sample
  - Sampling density preference

#### 3.3.3 Process
1. **Path Discretization**: Convert paths to dense point sequences
2. **Poisson Disk Sampling**: Apply Bridson's algorithm or similar:
   - Initialize active list with seed points
   - For each active point, generate candidate points in annulus
   - Accept candidates that maintain minimum distance from all existing points
   - Add accepted points to active list
   - Remove points that can no longer generate valid candidates
3. **Path Alignment**: Ensure sampled points follow path direction
4. **Density Adjustment**: Optionally adjust sampling density based on path curvature

#### 3.3.4 Output
- **Waypoint Positions**: Array of (x, y) coordinates representing drone positions
- **Ordering**: Sequence order for waypoint traversal
- **Metadata**: Total waypoints, average spacing, sampling parameters used

#### 3.3.5 Technical Requirements
- Poisson disk sampling implementation (custom or library)
- Efficient spatial data structures (k-d tree, grid) for distance queries
- Path traversal algorithms

#### 3.3.6 Constraints
- Minimum waypoint spacing must respect drone size and safety margins
- Maximum waypoint count limits to prevent excessive flight time
- Sampling must maintain path fidelity (not deviate significantly from original shape)

---

### 3.4 Stage 4: Physical Constraint Enforcement

#### 3.4.1 Purpose
Validate and adjust waypoints to ensure they satisfy physical constraints of drone flight, including speed limits, acceleration bounds, collision avoidance, and safety margins.

#### 3.4.2 Input
- Waypoint positions from Stage 3
- Physical parameters:
  - Maximum velocity (m/s)
  - Maximum acceleration (m/s²)
  - Minimum turn radius
  - Safety margins (distance from boundaries, obstacles)
  - Drone dimensions

#### 3.4.3 Process
1. **Velocity Profiling**: Calculate required velocities between waypoints
   - Check if velocities exceed maximum
   - Adjust waypoint spacing or add intermediate waypoints if needed
2. **Acceleration Validation**: Verify acceleration/deceleration requirements
   - Check if acceleration exceeds maximum
   - Insert intermediate waypoints for smooth transitions
3. **Turn Radius Validation**: Ensure turns respect minimum radius
   - Detect sharp turns
   - Smooth paths using Bézier curves or arc interpolation
4. **Collision Detection**: Check for self-intersections or boundary violations
   - Spatial queries for path intersections
   - Boundary checking against flight area limits
5. **Safety Margin Enforcement**: Ensure minimum distances from boundaries
   - Adjust waypoints that violate margins
   - Optionally reject paths that cannot be safely adjusted

#### 3.4.4 Output
- **Validated Waypoints**: Adjusted (x, y) positions meeting all constraints
- **Velocity Profile**: Speed assignments for each segment
- **Timing Information**: Estimated time per segment
- **Validation Report**: List of adjustments made, warnings, errors

#### 3.4.5 Technical Requirements
- Physics simulation or constraint solver
- Path smoothing algorithms (B-splines, Bézier curves)
- Spatial collision detection
- Numerical optimization for constraint satisfaction

#### 3.4.6 Constraints
- All waypoints must satisfy all physical constraints simultaneously
- Adjustments must preserve overall pattern shape as much as possible
- Safety margins are non-negotiable (hard constraints)

---

### 3.5 Stage 5: SkyBrush Export

#### 3.5.1 Purpose
Convert validated waypoints and flight parameters into SkyBrush Studio-compatible file format (.skyc or JSON).

#### 3.5.2 Input
- Validated waypoints from Stage 4
- Flight parameters (velocities, timing)
- Show metadata (name, description, duration)

#### 3.5.3 Process
1. **Format Mapping**: Map internal waypoint representation to SkyBrush format
2. **Coordinate Transformation**: Convert to SkyBrush coordinate system if needed
3. **Trajectory Generation**: Create trajectory objects with timing and positions
4. **Show Assembly**: Construct complete show structure:
   - Show metadata
   - Drone configuration
   - Trajectory definitions
   - Timing and synchronization
5. **File Serialization**: Write to SkyBrush-compatible format (JSON/XML)

#### 3.5.4 Output
- **SkyBrush File** (.skyc or .json): Complete flight show definition
- **Export Metadata**: Version info, export timestamp, compatibility notes

#### 3.5.5 Technical Requirements
- SkyBrush Studio file format specification/documentation
- JSON/XML serialization
- Coordinate system conversion utilities
- Format validation

#### 3.5.6 Constraints
- Output must be valid SkyBrush Studio format
- All required fields must be present
- Coordinate system must match SkyBrush expectations
- File must be importable without errors

---

## 4. Technical Specifications

### 4.1 Technology Stack
- **Language**: Python 3.10+
- **Core Libraries**:
  - `numpy`: Numerical operations, array handling
  - `pandas`: Data manipulation (if needed for metadata)
  - SVG processing: `svgpathtools`, `cairosvg`, or similar
  - Geometric algorithms: `shapely`, `scipy.spatial`
  - LLM integration: `openai`, `anthropic`, or similar API clients
- **Build System**: `uv` with `pyproject.toml`
- **Testing**: `pytest`
- **Linting**: `ruff`

### 4.2 Data Structures

#### Waypoint
```python
@dataclass
class Waypoint:
    x: float  # meters
    y: float  # meters
    z: float  # meters (altitude, may be constant)
    velocity: float  # m/s
    timestamp: float  # seconds from start
```

#### ProcessedPath
```python
@dataclass
class ProcessedPath:
    points: np.ndarray  # Shape: (N, 2) for (x, y) coordinates
    is_closed: bool
    metadata: dict
```

#### FlightShow
```python
@dataclass
class FlightShow:
    waypoints: list[Waypoint]
    metadata: dict
    constraints: dict
    skybrush_format: dict  # SkyBrush-compatible structure
```

### 4.3 Configuration
Configuration should be externalized (YAML/TOML) and include:
- LLM API keys and model selection
- Physical constraints (velocities, accelerations, safety margins)
- Sampling parameters (Poisson disk radius, density)
- SkyBrush export settings
- Coordinate system definitions

---

## 5. Error Handling

### 5.1 Stage-Specific Errors

**Stage 1 (LLM SVG)**:
- Invalid/malformed SVG: Retry with adjusted prompt or fallback to simpler generation
- API failures: Retry with exponential backoff, fallback to template-based generation
- Timeout: Return error with suggestion to simplify prompt

**Stage 2 (Geometry Processing)**:
- Invalid geometry: Attempt repair, or reject with error message
- Coordinate overflow: Scale down geometry, warn user
- Empty paths: Skip or warn, continue with valid paths

**Stage 3 (Poisson Sampling)**:
- Insufficient sampling: Reduce minimum distance or increase attempts
- Memory issues: Reduce path complexity or sampling density
- No valid samples: Fallback to uniform spacing

**Stage 4 (Constraint Enforcement)**:
- Unsatisfiable constraints: Return error with specific constraint violations
- Excessive adjustments: Warn user that pattern may be distorted
- Collision unavoidable: Reject path, suggest modifications

**Stage 5 (SkyBrush Export)**:
- Format errors: Validate and fix common issues, return detailed error if unfixable
- Missing required fields: Use defaults or return error
- Coordinate system mismatch: Transform or return error

### 5.2 User-Facing Errors
- Clear, actionable error messages
- Suggestions for resolution
- Logging for debugging (without exposing sensitive data)

---

## 6. Performance Requirements

### 6.1 Latency Targets
- Stage 1 (LLM): < 30 seconds (depends on API)
- Stage 2 (Geometry): < 1 second for typical SVGs
- Stage 3 (Sampling): < 5 seconds for 1000 waypoints
- Stage 4 (Constraints): < 10 seconds for validation
- Stage 5 (Export): < 1 second
- **Total Pipeline**: < 60 seconds for typical inputs

### 6.2 Scalability
- Support up to 10,000 waypoints per show
- Handle SVGs up to 10MB
- Process multiple shows in batch (future enhancement)

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Each pipeline stage independently testable
- Mock external dependencies (LLM API, file I/O)
- Test edge cases (empty inputs, malformed data, extreme values)

### 7.2 Integration Tests
- End-to-end pipeline with known inputs
- SkyBrush file validation (import into SkyBrush Studio)
- Regression tests for bug fixes

### 7.3 Test Data
- Sample prompts and expected outputs
- Known-good SVG files
- Reference SkyBrush files for comparison

---

## 8. Future Enhancements

### 8.1 Potential Additions
- **3D Flight Paths**: Support altitude variations
- **Multi-Drone Coordination**: Generate shows for multiple drones
- **Animation Support**: Time-varying patterns
- **Interactive Preview**: Visual preview before export
- **Pattern Library**: Pre-built templates for common shapes
- **Real-time Validation**: Live feedback during prompt input

### 8.2 Optimization Opportunities
- Parallel processing for independent path segments
- Caching of LLM responses for similar prompts
- Incremental processing for large shows
- GPU acceleration for geometric operations

---

## 9. Dependencies and External Services

### 9.1 Required Services
- LLM API (OpenAI GPT-4, Anthropic Claude, or local model)
- SkyBrush Studio (for validation/testing)

### 9.2 External Libraries
- See `pyproject.toml` for current dependencies
- Additional libraries may be needed:
  - SVG processing: `svgpathtools`, `cairosvg`
  - Geometry: `shapely`, `scipy`
  - LLM clients: `openai`, `anthropic`

---

## 10. Implementation Phases

### Phase 1: Core Pipeline (MVP)
- Stage 1: Basic LLM SVG generation
- Stage 2: Simple geometry processing
- Stage 3: Basic Poisson disk sampling
- Stage 4: Minimal constraint checking
- Stage 5: SkyBrush export (basic format)

### Phase 2: Robustness
- Enhanced error handling
- Comprehensive testing
- Performance optimization
- Documentation

### Phase 3: Advanced Features
- 3D paths
- Multi-drone support
- Interactive preview
- Pattern library

---

## 11. References

- [SkyBrush Studio Documentation](https://skybrush.io/)
- Poisson Disk Sampling: Bridson, R. (2007). "Fast Poisson disk sampling in arbitrary dimensions"
- SVG Specification: [W3C SVG 1.1](https://www.w3.org/TR/SVG11/)
- Douglas-Peucker Algorithm: Simplification of digitized curves

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-18 | Engineering Team | Initial specification |
