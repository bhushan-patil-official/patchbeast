"use client";
import * as React from "react";
import * as Tooltip from "@radix-ui/react-tooltip";
import { VERIFICATION } from "../lib/verification";
import { SignalMeter, type SignalMeterProps } from "./SignalMeter";

/** SignalMeter + keyboard-accessible tooltip explaining the verification rules (adds Radix Tooltip JS). */
export function ExplainedSignalMeter(props: SignalMeterProps) {
  return (
    <Tooltip.Provider delayDuration={150}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <button type="button" className="pb-focus rounded">
            <SignalMeter {...props} />
          </button>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            sideOffset={6}
            className="z-50 max-w-xs rounded border border-line bg-surface-3 px-3 py-2 text-xs text-fg shadow-2"
          >
            {VERIFICATION[props.level].help}
            <Tooltip.Arrow className="fill-surface-3" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
