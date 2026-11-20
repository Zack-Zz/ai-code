import { scopeChainOf, scopeOf } from '@deepseek-ai/dsh-scope'

export const name = 'codevow-reviewer-guard'
export const inject = ['tools', 'agents']
const allow = Object.freeze(['read', 'grep', 'glob'])

/** Native permission adapter; owns no model, execution loop or task state. */
export function apply(ctx) {
  const compositionScope = scopeOf(ctx)
  if (compositionScope === undefined) throw new Error(`${name}: requires a preset composition scope`)
  const agents = ctx.get('agents')
  if (!agents) throw new Error(`${name}: requires the agents registry`)
  const installed = new Map()
  const disposed = new WeakSet()
  let stopped = false
  const belongs = agent => !disposed.has(agent) &&
    scopeChainOf(scopeOf(agent.ctx)).includes(compositionScope)

  // A composition-level guard also rejects directly submitted/hidden tools.
  ctx.effect(() => ctx.tools.guard(exec => allow.includes(exec.name)
    ? undefined : `CodeVow Reviewer permits only read, grep and glob; denied ${exec.name}.`))

  function remove(agent) {
    const state = installed.get(agent)
    if (!state) return
    installed.delete(agent)
    state.dispose?.()
  }
  function install(agent) {
    if (stopped || !belongs(agent) || installed.has(agent)) return
    // restrict synchronously emits tools/change. Mark before entering it.
    const state = {}
    installed.set(agent, state)
    try {
      state.dispose = agent.ctx.tools.restrict({ allow: [...allow] })
    } catch (error) {
      installed.delete(agent)
      throw error // agent/created awaits us before any queued work is released.
    }
  }
  function reconcile() {
    if (stopped) return
    for (const agent of agents.list()) {
      try {
        if (belongs(agent)) install(agent)
        else remove(agent)
      } catch (error) {
        // The final composition guard stays installed when reconciliation fails.
        ctx.logger.warn(`${name}: failed to reconcile Agent "${agent.id}": ${String(error)}`)
      }
    }
  }
  ctx.on('agent/created', async ({ agent }) => { install(agent) })
  ctx.on('agent/disposed', ({ agent }) => { disposed.add(agent); remove(agent) })
  ctx.on('tools/change', reconcile)
  ctx.effect(() => () => {
    stopped = true
    for (const agent of installed.keys()) remove(agent)
  })
  // Loading into an existing/restored composition must also fail closed.
  for (const agent of agents.list()) install(agent)
}
