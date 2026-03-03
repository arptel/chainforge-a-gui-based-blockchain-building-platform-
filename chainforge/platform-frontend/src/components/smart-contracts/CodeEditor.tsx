import React, { useRef, useEffect } from 'react';
import Editor, { useMonaco } from '@monaco-editor/react';

interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
    language: 'python' | 'solidity';
    readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ value, onChange, language, readOnly = false }) => {
    const monaco = useMonaco();
    const editorRef = useRef<any>(null);
    const [isMounted, setIsMounted] = React.useState(false);

    useEffect(() => {
        setIsMounted(true);

        // Suppress Monaco Editor's internal "Canceled" promise rejections
        const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
            if (event.reason && typeof event.reason === 'object') {
                // Monaco often rejects with an object containing { name: 'Canceled' } or similar
                // when models are disposed. We prevent the Next.js overlay for these.
                if (event.reason.name === 'Canceled' || event.reason.message === 'Canceled') {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                } else if (!event.reason.message && !event.reason.stack) {
                    // Generic [object Object] that Monaco sometimes throws on worker abort
                    event.preventDefault();
                    event.stopImmediatePropagation();
                }
            }
        };
        // MUST use 'true' for capture phase to beat Next.js's global error overlay
        window.addEventListener('unhandledrejection', handleUnhandledRejection, true);
        return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection, true);
    }, []);

    useEffect(() => {
        try {
            if (monaco && editorRef.current && language === 'python') {
                validatePython(value);
            } else if (monaco && editorRef.current) {
                // clear markers if not python
                const model = editorRef.current.getModel();
                if (model && !model.isDisposed()) {
                    monaco.editor.setModelMarkers(model, 'owner', []);
                }
            }
        } catch (error) {
            console.error("Effect error:", error);
        }
    }, [value, language, monaco]);

    const handleEditorDidMount = (editor: any, monacoInstance: any) => {
        editorRef.current = editor;
        if (language === 'python') {
            validatePython(value);
        }
    };

    const validatePython = (code: string) => {
        try {
            if (!monaco || !editorRef.current) return;
            const model = editorRef.current.getModel();
            if (!model || model.isDisposed()) return;

            const markers: any[] = [];
            const lines = code.split('\n');

            lines.forEach((line, i) => {
                const num = i + 1;
                const trimmed = line.trim();

                // Ignore comments and empties
                if (trimmed.startsWith('#') || !trimmed) return;

                // Check for missing colons on block statements
                const blockKeywords = /^(def|class|if|elif|else|for|while|try|except|finally)\b/;
                if (blockKeywords.test(trimmed)) {
                    if (!trimmed.endsWith(':')) {
                        markers.push({
                            startLineNumber: num,
                            startColumn: line.length || 1,
                            endLineNumber: num,
                            endColumn: (line.length || 1) + 1,
                            message: "Syntax Error: Expected ':' at the end of the block statement.",
                            severity: monaco.MarkerSeverity.Error,
                        });
                    }
                }

                // Check for lowercase true/false/null
                const boolRegex = /\b(true|false|null)\b/;
                const boolMatch = line.match(boolRegex);
                if (boolMatch) {
                    markers.push({
                        startLineNumber: num,
                        startColumn: boolMatch.index! + 1,
                        endLineNumber: num,
                        endColumn: boolMatch.index! + 1 + boolMatch[0].length,
                        message: `Syntax Error: Use '${boolMatch[0] === 'null' ? 'None' : boolMatch[0].charAt(0).toUpperCase() + boolMatch[0].slice(1)}' in Python instead of '${boolMatch[0]}'`,
                        severity: monaco.MarkerSeverity.Error,
                    });
                }
            });

            if (!model.isDisposed()) {
                monaco.editor.setModelMarkers(model, 'owner', markers);
            }
        } catch (error) {
            console.error("Monaco validation error:", error);
        }
    };

    if (!isMounted) {
        return (
            <div className="relative font-mono text-sm border rounded-md overflow-hidden flex flex-col h-full min-h-[400px]">
                <div className="bg-muted px-4 py-2 text-xs text-muted-foreground uppercase border-b flex justify-between">
                    <span>{language}</span>
                    <span>Editor</span>
                </div>
                <div className="flex-1 bg-zinc-950 pt-2 flex items-center justify-center text-muted-foreground">
                    Loading editor...
                </div>
            </div>
        );
    }

    return (
        <div className="relative font-mono text-sm border rounded-md overflow-hidden flex flex-col h-full min-h-[400px]">
            <div className="bg-muted px-4 py-2 text-xs text-muted-foreground uppercase border-b flex justify-between">
                <span>{language}</span>
                <span>Editor</span>
            </div>
            <div className="flex-1 bg-zinc-950 pt-2">
                <Editor
                    height="100%"
                    language={language === 'solidity' ? 'sol' : 'python'}
                    theme="vs-dark"
                    value={value}
                    onChange={(val) => onChange(val || '')}
                    onMount={handleEditorDidMount}
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        wordWrap: 'on',
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                        readOnly: readOnly,
                    }}
                />
            </div>
        </div>
    );
};
