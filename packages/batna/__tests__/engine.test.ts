import { pickBand, compositeScore, DEFAULT_LEVERAGE } from '../engine'
import bandsData from '../seed/bands.json'

const PACK = bandsData as any

function findClause(key: string) {
  return PACK.clauses.find((c: any) => c.clause_key === key)
}

describe('ZOPA Engine - Comprehensive Tests', () => {
  // Basic functionality tests
  test('exclusivity 30 days should pick market band', () => {
    const c = findClause('exclusivity')
    const b = pickBand(c.bands, { value: 30 }, DEFAULT_LEVERAGE)
    expect(b).toBeDefined()
    expect(b?.name).toBe('market')
  })

  test('ROFR 10 days should pick short window band', () => {
    const c = findClause('rofr')
    const b = pickBand(c.bands, { value: 10 }, DEFAULT_LEVERAGE)
    expect(b).toBeDefined()
    expect(b?.name).toContain('short')
  })

  test('antidilution broad_wa should pick broad_wa band', () => {
    const c = findClause('antidilution')
    const b = pickBand(c.bands, { value: 'broad_wa' }, DEFAULT_LEVERAGE)
    expect(b).toBeDefined()
    expect(b?.name).toBe('broad_wa')
  })

  // Boundary and edge case tests
  test('exclusivity boundary cases', () => {
    const c = findClause('exclusivity')

    // Lower boundary of short range
    const b1 = pickBand(c.bands, { value: 15 }, DEFAULT_LEVERAGE)
    expect(b1?.name).toBe('short')

    // Upper boundary should pick market (tie-breaking)
    const b2 = pickBand(c.bands, { value: 30 }, DEFAULT_LEVERAGE)
    expect(b2?.name).toBe('market')

    // Upper boundary of market range
    const b3 = pickBand(c.bands, { value: 45 }, DEFAULT_LEVERAGE)
    expect(b3?.name).toBe('long')
  })

  test('enum matching for preemption', () => {
    const c = findClause('preemption')

    const b1 = pickBand(c.bands, { value: 'none' }, DEFAULT_LEVERAGE)
    expect(b1?.name).toBe('none')

    const b2 = pickBand(c.bands, { value: 'limited_next_round' }, DEFAULT_LEVERAGE)
    expect(b2?.name).toBe('market')

    const b3 = pickBand(c.bands, { value: 'full_ongoing' }, DEFAULT_LEVERAGE)
    expect(b3?.name).toBe('full')
  })

  // Composite scoring tests
  test('composite score calculation', () => {
    const band = { name: 'test', founder_score: 0.8, investor_score: 0.4 }
    const score = compositeScore(band, DEFAULT_LEVERAGE)
    // 0.4 * 0.6 + 0.8 * 0.4 = 0.24 + 0.32 = 0.56
    expect(score).toBe(0.56)
  })

  test('market band balanced scoring', () => {
    const c = findClause('exclusivity')
    const marketBand = c.bands.find((b: any) => b.name === 'market')
    const score = compositeScore(marketBand, DEFAULT_LEVERAGE)
    expect(Math.abs(score - 0.6)).toBeLessThan(0.001)
  })

  test('founder vs investor band scoring', () => {
    const c = findClause('exclusivity')
    const shortBand = c.bands.find((b: any) => b.name === 'short')
    const longBand = c.bands.find((b: any) => b.name === 'long')

    const founderScore = compositeScore(shortBand, DEFAULT_LEVERAGE)
    const investorScore = compositeScore(longBand, DEFAULT_LEVERAGE)

    expect(founderScore).toBeGreaterThan(0.6) // Founder gets higher weight
    expect(investorScore).toBeLessThan(0.6) // Investor gets lower weight
  })

  // Leverage sensitivity tests
  test('leverage sensitivity changes band selection', () => {
    const c = findClause('exclusivity')
    const founderLeverage = { investor: 0.3, founder: 0.7 }
    const investorLeverage = { investor: 0.8, founder: 0.2 }

    const b1 = pickBand(c.bands, { value: 30 }, founderLeverage)
    const b2 = pickBand(c.bands, { value: 30 }, investorLeverage)

    expect(b1?.name).toBe('short') // Founder-favored leverage picks founder band
    expect(b2?.name).toBe('long') // Investor-favored leverage picks investor band
  })

  // Market tie-breaking
  test('market tie-breaking preference', () => {
    const testBands = [
      { name: 'market', founder_score: 0.5, investor_score: 0.7, range: [10, 20] },
      { name: 'other', founder_score: 0.7, investor_score: 0.5, range: [10, 20] },
    ]

    // Both bands have same composite score (0.6), should prefer market
    const b = pickBand(testBands, { value: 15 }, DEFAULT_LEVERAGE)
    expect(b?.name).toBe('market')
  })

  // Posture classification tests
  test('posture classification logic', () => {
    // Founder-friendly band
    const founderBand = { name: 'founder_fav', founder_score: 0.9, investor_score: 0.3 }
    const founderScore = compositeScore(founderBand, DEFAULT_LEVERAGE)
    expect(founderScore).toBeGreaterThan(0.7) // Should be founder_friendly

    // Investor-friendly band
    const investorBand = { name: 'investor_fav', founder_score: 0.2, investor_score: 0.95 }
    const investorScore = compositeScore(investorBand, DEFAULT_LEVERAGE)
    expect(investorScore).toBeLessThan(0.4) // Should be investor_friendly

    // Market band (balanced)
    const marketBand = { name: 'balanced', founder_score: 0.55, investor_score: 0.65 }
    const marketScore = compositeScore(marketBand, DEFAULT_LEVERAGE)
    expect(marketScore).toBeGreaterThan(0.5)
    expect(marketScore).toBeLessThan(0.7)
  })

  // Edge cases
  test('no matching bands returns null', () => {
    const c = findClause('exclusivity')
    const b = pickBand(c.bands, { value: 100 }, DEFAULT_LEVERAGE)
    expect(b).toBeNull()
  })

  test('predicate-only bands work without value', () => {
    const c = findClause('drag')
    // Drag bands have predicates, should work without specific value
    const b = pickBand(c.bands, {}, DEFAULT_LEVERAGE)
    expect(b).toBeDefined()
  })

  test('invalid enum returns null', () => {
    const c = findClause('preemption')
    const b = pickBand(c.bands, { value: 'invalid_enum' }, DEFAULT_LEVERAGE)
    expect(b).toBeNull()
  })

  // Middle ground detection tests
  test('finds reasonable middle ground', () => {
    // Exclusivity 30 days = market (middle ground)
    const c1 = findClause('exclusivity')
    const b1 = pickBand(c1.bands, { value: 30 }, DEFAULT_LEVERAGE)
    expect(b1?.name).toBe('market')

    // Moderate ESOP pool
    const c2 = findClause('esop')
    const b2 = pickBand(c2.bands, { value: 12 }, DEFAULT_LEVERAGE)
    expect(b2?.name).toBe('post_money_8_12')

    // Balanced board
    const c3 = findClause('board')
    const b3 = pickBand(c3.bands, { value: 'balanced' }, DEFAULT_LEVERAGE)
    expect(b3?.name).toBe('market')
  })

  // Comprehensive clause coverage
  test('all major clause types work', () => {
    const testCases = [
      ['exclusivity', { value: 30 }, 'market'],
      ['preemption', { value: 'limited_next_round' }, 'market'],
      ['rofo', { value: 20 }, 'market'],
      ['rofr', { value: 20 }, 'market'],
      ['tag', { value: 'pro_rata_only' }, 'market'],
      ['antidilution', { value: 'broad_wa' }, 'broad_wa'],
      ['affirmative_rights', { value: 'market_list' }, 'market'],
      ['exit', { value: 4 }, 'market'],
      ['liq_pref', { value: '1x_np' }, 'market'],
      ['board', { value: 'balanced' }, 'market'],
      ['info_rights', { value: 'monthly_kpi_q_fin' }, 'market'],
      ['esop', { value: 12 }, 'post_money_8_12'],
      ['pay_to_play', { value: 'soft' }, 'market'],
    ]

    testCases.forEach(([clauseKey, attrs, expectedBand]) => {
      const clause = findClause(clauseKey as string)
      const band = pickBand(clause.bands, attrs as any, DEFAULT_LEVERAGE)
      expect(band).toBeDefined()
      expect(band?.name).toBe(expectedBand)
    })
  })

  // Liquidation preference specific tests
  test('liquidation preference scoring hierarchy', () => {
    const c = findClause('liq_pref')

    const b1 = pickBand(c.bands, { value: '1x_np' }, DEFAULT_LEVERAGE)
    expect(b1?.name).toBe('market')

    const b2 = pickBand(c.bands, { value: '1x_p' }, DEFAULT_LEVERAGE)
    expect(b2?.name).toBe('investor_plus')

    const b3 = pickBand(c.bands, { value: '>1x_p' }, DEFAULT_LEVERAGE)
    expect(b3?.name).toBe('heavy_p')
  })

  // Range boundary tests
  test('range boundary behavior', () => {
    const c = findClause('exit')

    // Lower boundary of long_fuse
    const b1 = pickBand(c.bands, { value: 5 }, DEFAULT_LEVERAGE)
    expect(b1?.name).toBe('long_fuse')

    // Upper boundary of market
    const b2 = pickBand(c.bands, { value: 5 }, DEFAULT_LEVERAGE)
    expect(b2?.name).toBe('market')

    // Upper boundary of short_fuse
    const b3 = pickBand(c.bands, { value: 4 }, DEFAULT_LEVERAGE)
    expect(b3?.name).toBe('short_fuse')
  })
})
