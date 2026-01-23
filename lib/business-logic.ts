
export const CTR_CURVE: Record<number, number> = {
    1: 0.32, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05,
    6: 0.04, 7: 0.03, 8: 0.03, 9: 0.02, 10: 0.02
};

export function classifyIntent(keyword: string): string {
    const k = keyword.toLowerCase();
    if (k.match(/\b(buy|price|cost|cheap|deal|sale|discount|hiring|services|agency)\b/)) return 'Commercial';
    if (k.match(/\b(how|what|why|guide|tutorial|examples|tips|best)\b/)) return 'Informational';
    if (k.match(/\b(review|vs|comparison|best)\b/)) return 'Investigation'; // Mixed/Investigation
    return 'Informational'; // Default fallback
}

export function calculateUplift(position: number, volume: number, cpc: number): number {
    if (position <= 3) return 0; // Already in top 3, no significant uplift calc for this specific "Striking Distance" metric

    const currentCtr = CTR_CURVE[position] || 0.01;
    const potentialCtr = CTR_CURVE[3]; // Aiming for Top 3

    const currentTraffic = volume * currentCtr;
    const potentialTraffic = volume * potentialCtr;

    const trafficGain = potentialTraffic - currentTraffic;
    return trafficGain * cpc; // Value in local currency
}

export function recommendAction(position: number, trend: 'up' | 'down' | 'stable', intent: string): string {
    if (position >= 4 && position <= 10) {
        if (intent === 'Commercial') return 'Reforzar (Money Keyword)';
        return 'Optimizar CTR';
    }
    if (position > 10 && position <= 20) {
        return 'Crear Contenido Apoyo';
    }
    if (trend === 'down') return 'Investigar Caída - Proteger';

    return 'Monitorizar';
}
