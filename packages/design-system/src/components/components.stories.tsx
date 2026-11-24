import * as React from "react";
import type { Meta, StoryObj } from "@storybook/react";
import { AdSlot } from "./AdSlot";
import { BeastMark, Wordmark } from "./BeastMark";
import { Button } from "./Button";
import { Card, Section } from "./Card";
import { ChangeLog } from "./ChangeLog";
import { Countdown } from "./Countdown";
import { HardwareCard } from "./HardwareCard";
import { SignalMeter } from "./SignalMeter";
import { ExplainedSignalMeter } from "./ExplainedSignalMeter";
import { SourceChip } from "./SourceChip";
import { SpecCompare } from "./SpecCompare";
import { StatusTicker } from "./StatusTicker";
import { ThemeToggle } from "./ThemeToggle";

const inDays = (d: number) => new Date(Date.now() + d * 86400000).toISOString();

const meta: Meta = { title: "Patchbeast/Overview", parameters: { layout: "padded" } };
export default meta;
type S = StoryObj;

export const Brand: S = {
  render: () => (
    <div className="flex items-center gap-8">
      <Wordmark />
      <BeastMark size={64} />
    </div>
  ),
};

export const Buttons: S = {
  render: () => (
    <div className="flex gap-3">
      <Button>Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button disabled>Disabled</Button>
    </div>
  ),
};

export const CountdownLive: S = { render: () => <Countdown target={inDays(42)} mode="live" /> };
export const CountdownUnconfirmed: S = {
  name: "Countdown (rumour: frozen honestly)",
  render: () => <Countdown target={null} mode="unconfirmed" />,
};

export const SignalMeters: S = {
  render: () => (
    <div className="flex flex-col items-start gap-3">
      <ExplainedSignalMeter level="confirmed" sources={2} />
      <SignalMeter level="reported" sources={1} />
      <SignalMeter level="rumour" />
      <SignalMeter level="confirmed" sources={3} size="sm" />
    </div>
  ),
};

export const SourceChips: S = {
  render: () => (
    <div className="flex gap-3">
      <SourceChip url="https://news.example.com/post/1" name="Example News" />
      <SourceChip url="https://www.example.org/a/very/long/path" />
    </div>
  ),
};

export const ChangeLogStory: S = {
  name: "ChangeLog",
  render: () => (
    <div className="w-[34rem]">
      <ChangeLog
        entries={[
          { id: 1, title: "Patch 0.9.1", versionLabel: "0.9.1", detail: "Fixes shader stutter on first launch.", occurredAt: inDays(-3), sourceUrl: "https://example.com/p", verification: "confirmed" },
          { id: 2, title: "Release date updated", detail: "unknown -> 2027-03-01", occurredAt: inDays(-9), sourceUrl: "https://example.com/d", verification: "reported" },
          { id: 3, title: "Minimum requirements published", occurredAt: inDays(-20), verification: "rumour" },
        ]}
      />
    </div>
  ),
};

export const Ticker: S = {
  parameters: { layout: "fullscreen" },
  render: () => (
    <StatusTicker
      items={[
        { id: 1, game: "DEMO", text: "Patch 0.9.1 released", href: "#" },
        { id: 2, game: "DEMO", text: "Release date now Confirmed: 2027-03-01", href: "#" },
        { id: 3, game: "DEMO", text: "Recommended requirements published", href: "#" },
      ]}
    />
  ),
};

export const Hardware: S = {
  render: () => (
    <div className="w-80">
      <HardwareCard category="GPU" title="Example 12 GB graphics card" blurb="Sample block. Only shown when affiliate is configured." merchant="Example Store" href="https://example.com" price="$329" />
    </div>
  ),
};

export const AdSlotStory: S = {
  name: "AdSlot (reserved height, flag-gated)",
  render: () => (
    <div className="w-[22rem]">
      <p className="mb-2 text-sm text-fg-muted">Flag off → renders nothing. Flag on → reserved 250px.</p>
      <AdSlot enabled height={250}>
        <span className="text-xs text-fg-muted">ad unit</span>
      </AdSlot>
      <AdSlot enabled={false} height={250}>
        <span>never shown</span>
      </AdSlot>
    </div>
  ),
};

export const Specs: S = {
  render: () => (
    <div className="w-[44rem]">
      <SpecCompare
        min={{ os: "Windows 10", cpu: "Quad-core 3.0 GHz", gpu: "6 GB VRAM class", ramGb: 8, storageGb: 60, verification: "reported", sources: 1, sourceUrl: "https://example.com/r" }}
        rec={{ verification: "rumour" }}
      />
    </div>
  ),
};

export const Surfaces: S = {
  render: () => (
    <Section eyebrow="Layered surfaces" title="Mission console">
      <div className="flex gap-3">
        {["bg-surface-1", "bg-surface-2", "bg-surface-3"].map((c) => (
          <Card key={c} className={`${c} h-20 w-32 p-3 font-mono text-xs`}>
            {c}
          </Card>
        ))}
        <ThemeToggle />
      </div>
    </Section>
  ),
};
