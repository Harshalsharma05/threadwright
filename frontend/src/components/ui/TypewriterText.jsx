import React from 'react';

// --- Typewriter Component (Word-by-Word Reveal) ---
export const TypewriterText = ({ text, delayOffset = 0, highlightKeywords = [] }) => {
    if (!text) return null;

    let tokens = [];

    if (highlightKeywords && highlightKeywords.length > 0) {
        // Split text based on keywords while keeping the keywords in the array
        const regex = new RegExp(`(${highlightKeywords.join('|')})`, 'gi');
        const parts = text.split(regex);

        parts.forEach(part => {
            const isMatch = highlightKeywords.some(k => k.toLowerCase() === part.toLowerCase());
            
            // Split everything by spaces so every single word wraps perfectly
            const words = part.split(' ');
            words.forEach(word => {
                if (word !== '') {
                    tokens.push({ text: word, isHighlight: isMatch });
                }
            });
        });
    } else {
        // No keywords, just split by spaces
        const words = text.split(' ');
        words.forEach(word => {
            if (word !== '') {
                tokens.push({ text: word, isHighlight: false });
            }
        });
    }

    return (
        <>
            {tokens.map((token, i) => (
                <span key={i}>
                    <span 
                        className={`inline-block opacity-0 animate-[revealWord_0.1s_ease-out_forwards] ${
                            token.isHighlight ? 'text-cyan-400 font-bold tracking-wide' : ''
                        }`} 
                        style={{ animationDelay: `${delayOffset + (i * 15)}ms` }} // 15ms per word
                    >
                        {token.text}
                    </span>
                    {/* The crucial space goes OUTSIDE the inline-block so the browser wraps properly */}
                    {' '}
                </span>
            ))}
        </>
    );
};