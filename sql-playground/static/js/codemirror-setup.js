/**
 * CodeMirror Setup and Configuration
 * SQL syntax highlighting with SQL keywords
 */

const SQL_KEYWORDS = {
    keywords: 'SELECT,FROM,WHERE,AND,OR,NOT,IN,LIKE,BETWEEN,IS,NULL,AS,ON,JOIN,LEFT,RIGHT,INNER,OUTER,FULL,CROSS,UNION,ALL,DISTINCT,GROUP,BY,HAVING,ORDER,ASC,DESC,LIMIT,OFFSET,INSERT,INTO,VALUES,UPDATE,SET,DELETE,CREATE,TABLE,INDEX,DROP,ALTER,ADD,COLUMN,PRIMARY,KEY,FOREIGN,REFERENCES,CONSTRAINT,DEFAULT,AUTOINCREMENT,INTEGER,TEXT,REAL,BLOB,BOOLEAN,DATE,DATETIME,TIMESTAMP,VIEW,TRIGGER',
    builtin: 'COUNT,SUM,AVG,MIN,MAX,TOTAL,COALESCE,IFNULL,NULLIF,CAST,SUBSTR,SUBSTRING,LENGTH,UPPER,LOWER,TRIM,REPLACE,ABS,ROUND,RANDOM,RAND,DATE,TIME,DATETIME,STRFTIME,JULIANDAY,TYPEOF,LAST_INSERT_ROWID',
    operators: '=,<,>,<=,>=,!=,<>,||'
};

/**
 * Initialize CodeMirror editor
 * @param {HTMLElement} container - Container element for the editor
 * @param {Object} options - Editor options
 * @returns {CodeMirror} The created editor instance
 */
function initCodeMirror(container, options = {}) {
    const textarea = document.createElement('textarea');
    container.appendChild(textarea);
    
    const defaultOptions = {
        mode: 'text/x-sql',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: false,
        autofocus: true,
        indentWithTabs: false,
        tabSize: 2,
        indentUnit: 2,
        autoCloseBrackets: true,
        matchBrackets: true,
        syntaxHighlighting: true,
        keyMap: 'default'
    };
    
    const editor = CodeMirror.fromTextArea(textarea, { ...defaultOptions, ...options });
    
    // Add Ctrl+Enter / Cmd+Enter to execute
    editor.addKeyMap({
        'Ctrl-Enter': function(cm) {
            if (window.executeQuery) {
                window.executeQuery();
            }
        },
        'Cmd-Enter': function(cm) {
            if (window.executeQuery) {
                window.executeQuery();
            }
        },
        // Tab to insert spaces
        'Tab': function(cm) {
            if (cm.somethingSelected()) {
                cm.indentSelection('add');
            } else {
                var spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
                cm.replaceSelection(spaces);
            }
        }
    });
    
    return editor;
}

/**
 * Get cursor position info
 * @param {CodeMirror} editor - The editor instance
 * @returns {string} Position string
 */
function getCursorPosition(editor) {
    var cursor = editor.getCursor();
    return 'Ln ' + cursor.line + ', Col ' + cursor.ch;
}

/**
 * Format SQL query
 * @param {string} sql - Raw SQL query
 * @returns {string} Formatted SQL
 */
function formatSQL(sql) {
    if (!sql) return '';
    
    var keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER BY', 'GROUP BY', 
                    'HAVING', 'LIMIT', 'OFFSET', 'INSERT INTO', 'VALUES', 'UPDATE', 
                    'SET', 'DELETE FROM', 'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE',
                    'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
                    'ON', 'AS', 'DISTINCT', 'UNION', 'ALL', 'INTO', 'PRIMARY KEY',
                    'FOREIGN KEY', 'REFERENCES', 'NOT NULL', 'DEFAULT', 'UNIQUE'];
    
    var result = sql;
    
    // Uppercase keywords
    keywords.forEach(function(keyword) {
        var regex = new RegExp('\\b' + keyword + '\\b', 'gi');
        result = result.replace(regex, keyword);
    });
    
    // Add newlines before major keywords
    var newlineKeywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER BY', 'GROUP BY', 
                           'HAVING', 'LIMIT', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
                           'INNER JOIN', 'INSERT INTO', 'VALUES', 'UPDATE', 'SET',
                           'DELETE FROM', 'UNION'];
    
    newlineKeywords.forEach(function(keyword) {
        var regex = new RegExp('\\s+' + keyword + '\\b', 'gi');
        result = result.replace(regex, '\n' + keyword);
    });
    
    // Clean up multiple newlines
    result = result.replace(/\n{3,}/g, '\n\n');
    
    // Trim
    result = result.trim();
    
    return result;
}

// Export functions for use in app.js
window.initCodeMirror = initCodeMirror;
window.getCursorPosition = getCursorPosition;
window.formatSQL = formatSQL;
window.SQL_KEYWORDS = SQL_KEYWORDS;
