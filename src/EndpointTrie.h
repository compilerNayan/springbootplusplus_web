#ifndef ENDPOINT_TRIE_H
#define ENDPOINT_TRIE_H

#include <StandardDefines.h>
#include <map>
#include <vector>

/**
 * Result structure returned when matching an endpoint
 */
struct EndpointMatchResult {
    StdString pattern;  // The matched endpoint pattern (e.g., "/api/user/{userId}/get")
    Map<StdString, StdString> variables;  // Map of variable names to values (e.g., {"userId": "123"})
    Bool found;  // Whether a match was found
    
    EndpointMatchResult() : found(false) {}
    EndpointMatchResult(const StdString& pat, const Map<StdString, StdString>& vars) 
        : pattern(pat), variables(vars), found(true) {}
};

/**
 * Trie node for storing endpoint patterns
 */
class EndpointTrieNode {
    Private
        // Children for literal path segments (e.g., "user", "api")
        Map<StdString, EndpointTrieNode*> literalChildren;
        
        // Child for variable path segments (e.g., "{userId}")
        // Stores the variable name and the child node
        Map<StdString, EndpointTrieNode*> variableChildren;  // key: variable name, value: child node
        
        // Endpoint pattern stored at this node (if this is a leaf)
        StdString endpointPattern;
        
        // Whether this node represents a complete endpoint
        Bool isEndpoint;
        
        // Count of literal children (for IsEmpty check)
        Size literalChildrenCount;

    Public
        EndpointTrieNode() : isEndpoint(false), literalChildrenCount(0) {}
        
        ~EndpointTrieNode() {
            // Clean up literal children
            for (auto& pair : literalChildren) {
                delete pair.second;
            }
            // Clean up variable children
            for (auto& pair : variableChildren) {
                delete pair.second;
            }
        }
        
        // Get or create a literal child node
        EndpointTrieNode* GetOrCreateLiteralChild(const StdString& segment) {
            if (literalChildren.find(segment) == literalChildren.end()) {
                literalChildren[segment] = new EndpointTrieNode();
                literalChildrenCount++;
            }
            return literalChildren[segment];
        }
        
        // Get or create a variable child node
        EndpointTrieNode* GetOrCreateVariableChild(const StdString& variableName) {
            if (variableChildren.find(variableName) == variableChildren.end()) {
                variableChildren[variableName] = new EndpointTrieNode();
            }
            return variableChildren[variableName];
        }
        
        // Get literal child if exists
        EndpointTrieNode* GetLiteralChild(const StdString& segment) const {
            auto it = literalChildren.find(segment);
            if (it != literalChildren.end()) {
                return it->second;
            }
            return nullptr;
        }
        
        // Get all variable children (for matching)
        const Map<StdString, EndpointTrieNode*>& GetVariableChildren() const {
            return variableChildren;
        }
        
        // Set endpoint pattern at this node
        Void SetEndpointPattern(const StdString& pattern) {
            endpointPattern = pattern;
            isEndpoint = true;
        }
        
        // Get endpoint pattern
        StdString GetEndpointPattern() const {
            return endpointPattern;
        }
        
        // Check if this is an endpoint node
        Bool IsEndpoint() const {
            return isEndpoint;
        }
        
        // Get count of literal children
        Size GetLiteralChildrenCount() const {
            return literalChildrenCount;
        }
        
        // Check if node has any children
        Bool HasChildren() const {
            return literalChildrenCount > 0 || !variableChildren.empty();
        }
};

/**
 * Trie data structure for storing and matching HTTP endpoint patterns with path variables
 * 
 * Supports patterns like:
 * - /api/user/create
 * - /api/user/{userId}/get
 * - /hello/{mno}/{pqr}/{def}
 * 
 * Can match actual paths like:
 * - /api/user/123/get -> matches /api/user/{userId}/get with variables {"userId": "123"}
 */
class EndpointTrie {
    Private
        EndpointTrieNode* root;
        
        /**
         * Split a path into segments
         * "/api/user/create" -> ["api", "user", "create"]
         * "/api/user/123/" -> ["api", "user", "123", ""] (empty segment for trailing slash)
         * "/api//user" -> ["api", "user"] (empty segments from // are filtered out)
         */
        Vector<StdString> SplitPath(const StdString& path) const {
            Vector<StdString> segments;
            if (path.empty() || path == "/") {
                return segments;
            }
            
            StdString current = path;
            // Remove leading slash
            if (current[0] == '/') {
                current = current.substr(1);
            }
            
            // Check if there's a trailing slash (we'll preserve it as an empty segment)
            Bool hasTrailingSlash = !current.empty() && current[current.length() - 1] == '/';
            
            // Remove trailing slash temporarily for splitting
            if (hasTrailingSlash) {
                current = current.substr(0, current.length() - 1);
            }
            
            // Split by '/'
            size_t start = 0;
            while (start < current.length()) {
                size_t pos = current.find('/', start);
                if (pos == StdString::npos) {
                    StdString segment = current.substr(start);
                    // Only add non-empty segments (filters out empty segments from // in middle)
                    if (!segment.empty()) {
                        segments.push_back(segment);
                    }
                    break;
                } else {
                    StdString segment = current.substr(start, pos - start);
                    // Only add non-empty segments (handles multiple slashes like "//")
                    if (!segment.empty()) {
                        segments.push_back(segment);
                    }
                    start = pos + 1;
                }
            }
            
            // Add empty segment at the end if there was a trailing slash
            // This distinguishes "/api/user/123" from "/api/user/123/"
            if (hasTrailingSlash) {
                segments.push_back("");
            }
            
            return segments;
        }
        
        /**
         * Check if a segment is a variable (starts with '{' and ends with '}')
         */
        Bool IsVariableSegment(const StdString& segment) const {
            return segment.length() >= 2 && 
                   segment[0] == '{' && 
                   segment[segment.length() - 1] == '}';
        }
        
        /**
         * Extract variable name from segment
         * "{userId}" -> "userId"
         */
        StdString ExtractVariableName(const StdString& segment) const {
            if (IsVariableSegment(segment)) {
                return segment.substr(1, segment.length() - 2);
            }
            return "";
        }
        
        /**
         * Recursive search helper
         */
        EndpointMatchResult SearchRecursive(
            EndpointTrieNode* node,
            const Vector<StdString>& segments,
            size_t index,
            Map<StdString, StdString>& variables
        ) const {
            // If we've processed all segments
            if (index >= segments.size()) {
                if (node->IsEndpoint()) {
                    return EndpointMatchResult(node->GetEndpointPattern(), variables);
                }
                return EndpointMatchResult();  // No match
            }
            
            StdString currentSegment = segments[index];
            
            // Special handling for empty segment (trailing slash)
            // If we encounter an empty segment, prefer exact endpoint match over variable match
            // This handles the case where /xyz/ should match /xyz instead of /xyz/{ssid}
            if (currentSegment.empty()) {
                // If we're at the last segment (trailing slash at end of path)
                if (index + 1 >= segments.size()) {
                    // Only match if current node is an endpoint AND we haven't consumed any variables
                    // This ensures:
                    // - /xyz/ matches /xyz (exact literal match, no variables consumed)
                    // - /api/user/123/ does NOT match /api/user/{userId} (variable was consumed)
                    if (node->IsEndpoint() && variables.empty()) {
                        return EndpointMatchResult(node->GetEndpointPattern(), variables);
                    }
                    // If we consumed variables or node is not an endpoint, no match
                    // This ensures paths with trailing slash don't match patterns without trailing slash
                    // when variables were consumed
                    return EndpointMatchResult();  // No match - trailing slash doesn't match pattern
                }
                // If there are more segments after the empty one, try variable match
                // (This handles cases like /api/{var}//something, though uncommon)
                const Map<StdString, EndpointTrieNode*>& varChildren = node->GetVariableChildren();
                for (const auto& pair : varChildren) {
                    StdString varName = pair.first;
                    EndpointTrieNode* varChild = pair.second;
                    
                    // Store the variable value (empty string for trailing slash)
                    variables[varName] = currentSegment;
                    
                    // Continue search with next segment
                    EndpointMatchResult result = SearchRecursive(varChild, segments, index + 1, variables);
                    if (result.found) {
                        return result;
                    }
                    
                    // Backtrack: remove the variable we just tried
                    variables.erase(varName);
                }
                return EndpointMatchResult();  // No match
            }
            
            // For non-empty segments, try literal match first
            EndpointTrieNode* literalChild = node->GetLiteralChild(currentSegment);
            if (literalChild != nullptr) {
                EndpointMatchResult result = SearchRecursive(literalChild, segments, index + 1, variables);
                if (result.found) {
                    return result;
                }
            }
            
            // Try variable match (try all variable children)
            const Map<StdString, EndpointTrieNode*>& varChildren = node->GetVariableChildren();
            for (const auto& pair : varChildren) {
                StdString varName = pair.first;
                EndpointTrieNode* varChild = pair.second;
                
                // Store the variable value
                variables[varName] = currentSegment;
                
                // Continue search
                EndpointMatchResult result = SearchRecursive(varChild, segments, index + 1, variables);
                if (result.found) {
                    return result;
                }
                
                // Backtrack: remove the variable we just tried
                variables.erase(varName);
            }
            
            return EndpointMatchResult();  // No match
        }

    Public
        EndpointTrie() {
            root = new EndpointTrieNode();
        }
        
        ~EndpointTrie() {
            delete root;
        }
        
        /**
         * Insert an endpoint pattern into the trie
         * 
         * @param pattern The endpoint pattern (e.g., "/api/user/{userId}/get")
         */
        Void Insert(const StdString& pattern) {
            Vector<StdString> segments = SplitPath(pattern);
            EndpointTrieNode* current = root;
            
            for (const StdString& segment : segments) {
                if (IsVariableSegment(segment)) {
                    StdString varName = ExtractVariableName(segment);
                    current = current->GetOrCreateVariableChild(varName);
                } else {
                    current = current->GetOrCreateLiteralChild(segment);
                }
            }
            
            // Mark as endpoint
            current->SetEndpointPattern(pattern);
        }
        
        /**
         * Search for a matching endpoint pattern
         * 
         * @param path The actual path to match (e.g., "/api/user/123/get")
         * @return EndpointMatchResult containing the matched pattern and variable values
         */
        EndpointMatchResult Search(const StdString& path) const {
            Vector<StdString> segments = SplitPath(path);
            Map<StdString, StdString> variables;
            return SearchRecursive(root, segments, 0, variables);
        }
        
        /**
         * Check if the trie is empty
         */
        Bool IsEmpty() const {
            return !root->IsEndpoint() && !root->HasChildren();
        }
        
        /**
         * Clear all endpoints from the trie
         */
        Void Clear() {
            delete root;
            root = new EndpointTrieNode();
        }
};

#endif // ENDPOINT_TRIE_H

