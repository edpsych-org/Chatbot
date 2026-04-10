"use client";

import { useState, useCallback } from "react";

interface ConfirmState {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  variant: "danger" | "default";
  resolve: ((value: boolean) => void) | null;
}

export function useConfirm() {
  const [state, setState] = useState<ConfirmState>({
    open: false,
    title: "Confirm Action",
    message: "",
    confirmLabel: "Continue",
    variant: "default",
    resolve: null,
  });

  const confirm = useCallback(
    (
      message: string,
      options?: {
        title?: string;
        confirmLabel?: string;
        variant?: "danger" | "default";
      }
    ): Promise<boolean> => {
      return new Promise((resolve) => {
        setState({
          open: true,
          title: options?.title ?? "Confirm Action",
          message,
          confirmLabel: options?.confirmLabel ?? "Continue",
          variant: options?.variant ?? "default",
          resolve,
        });
      });
    },
    []
  );

  const handleConfirm = useCallback(() => {
    state.resolve?.(true);
    setState((s) => ({ ...s, open: false, resolve: null }));
  }, [state]);

  const handleCancel = useCallback(() => {
    state.resolve?.(false);
    setState((s) => ({ ...s, open: false, resolve: null }));
  }, [state]);

  return {
    confirm,
    confirmProps: {
      open: state.open,
      title: state.title,
      message: state.message,
      confirmLabel: state.confirmLabel,
      variant: state.variant,
      onConfirm: handleConfirm,
      onCancel: handleCancel,
    },
  };
}
