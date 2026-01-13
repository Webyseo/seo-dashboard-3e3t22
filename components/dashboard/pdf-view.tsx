/* eslint-disable jsx-a11y/alt-text */
'use client'
import { Document, Page, Text, View, StyleSheet, Font } from '@react-pdf/renderer'
import { ExecutiveSummaryData } from '@/lib/data-service'

// Register fonts if needed, or use standard Helvetica
Font.register({
    family: 'Helvetica',
    fonts: [{ src: 'https://fonts.gstatic.com/s/helveticaneue/v70/1Ptsg8zYS_SKggPNyC0IT4ttDfA.ttf' }] // Example or stick to defaults
})

const styles = StyleSheet.create({
    page: { flexDirection: 'column', backgroundColor: '#ffffff', padding: 30, fontFamily: 'Helvetica' },
    header: { fontSize: 24, marginBottom: 10, fontWeight: 'bold', color: '#1e293b' },
    subheader: { fontSize: 12, marginBottom: 20, color: '#64748b' },
    sectionTitle: { fontSize: 16, marginTop: 15, marginBottom: 5, fontWeight: 'bold', color: '#334155' },
    row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
    kpiBox: { width: '23%', padding: 10, backgroundColor: '#f1f5f9', borderRadius: 4 },
    kpiTitle: { fontSize: 10, color: '#64748b' },
    kpiValue: { fontSize: 18, fontWeight: 'bold', color: '#0f172a' },
    table: { marginTop: 10 },
    tableRow: { flexDirection: 'row', borderBottomWidth: 1, borderColor: '#e2e8f0', paddingVertical: 4 },
    tableHeader: { fontSize: 10, color: '#64748b', fontWeight: 'bold' },
    tableCell: { fontSize: 10, color: '#334155' },
    insightBox: { padding: 10, backgroundColor: '#f0fdf4', marginBottom: 5, borderRadius: 4, flexDirection: 'row' },
    insightText: { fontSize: 10, color: '#166534' }
})

interface PdfProps {
    data: ExecutiveSummaryData
    period: string
    project: string
}

export const ExecutivePdf = ({ data, period, project }: PdfProps) => (
    <Document>
        <Page size="A4" style={styles.page}>
            <Text style={styles.header}>Executive Summary: {project}</Text>
            <Text style={styles.subheader}>Period: {period} | Generated: {new Date().toLocaleDateString()}</Text>

            <Text style={styles.sectionTitle}>Key Performance Indicators</Text>
            <View style={styles.row}>
                <View style={styles.kpiBox}>
                    <Text style={styles.kpiTitle}>Share of Voice</Text>
                    <Text style={styles.kpiValue}>{data.sov.toFixed(2)}%</Text>
                </View>
                <View style={styles.kpiBox}>
                    <Text style={styles.kpiTitle}>Total Visibility</Text>
                    <Text style={styles.kpiValue}>{data.totalVisibility.toFixed(0)}</Text>
                </View>
                <View style={styles.kpiBox}>
                    <Text style={styles.kpiTitle}>Top 10 Keywords</Text>
                    <Text style={styles.kpiValue}>{data.top10}</Text>
                </View>
                <View style={styles.kpiBox}>
                    <Text style={styles.kpiTitle}>Striking Distance</Text>
                    <Text style={styles.kpiValue}>{data.strikingDistance}</Text>
                </View>
            </View>

            <Text style={styles.sectionTitle}>Insights & Actions</Text>
            <View style={styles.insightBox}>
                <Text style={styles.insightText}>• Visibility is stable. Focus on the {data.strikingDistance} keywords in Striking Distance (Pos 4-10).</Text>
            </View>
            <View style={{ ...styles.insightBox, backgroundColor: '#eff6ff' }}>
                <Text style={{ ...styles.insightText, color: '#1e40af' }}>• {data.top3} Keywords are dominating in the Top 3 positions.</Text>
            </View>

            <Text style={styles.sectionTitle}>Performance Breakdown</Text>
            <View style={styles.table}>
                <View style={styles.tableRow}>
                    <Text style={{ ...styles.tableHeader, width: '50%' }}>Metric</Text>
                    <Text style={{ ...styles.tableHeader, width: '50%' }}>Value</Text>
                </View>
                <View style={styles.tableRow}>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>Keywords in Top 3</Text>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>{data.top3}</Text>
                </View>
                <View style={styles.tableRow}>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>Keywords in Top 20</Text>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>{data.top20}</Text>
                </View>
                <View style={styles.tableRow}>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>Average Position</Text>
                    <Text style={{ ...styles.tableCell, width: '50%' }}>{data.avgPosition.toFixed(1)}</Text>
                </View>
            </View>

            <Text style={{ position: 'absolute', bottom: 30, left: 30, fontSize: 10, color: '#94a3b8' }}>
                Confidential - Internal Use Only
            </Text>
        </Page>
    </Document>
)
