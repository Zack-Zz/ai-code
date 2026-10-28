import { Service } from '@deepseek-ai/cordis';
import AgentPreset from '@deepseek-ai/dsh-agent-preset';

/** Keep the native preset lifecycle and publish its registration as a dependency. */
export default class ReviewerPreset extends AgentPreset {
  #owner;

  constructor(ctx, config) {
    super(ctx, config);
    this.#owner = ctx;
  }

  async [Service.init]() {
    const lifecycle = super[Service.init]();
    const ctx = this.#owner;
    // One effect releases in reverse order: revoke delegation, then unregister
    // the preset. Independent top-level effects would dispose concurrently.
    await ctx.effect(async function* () {
      yield* lifecycle;
      yield ctx.provide('codevowReviewerPresetRegistered', true);
    }, 'codevow.reviewer-preset');
  }
}
