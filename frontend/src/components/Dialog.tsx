import { useEffect, useId, useRef, type ReactNode } from "react";

export default function Dialog({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current!;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} className="dialog" aria-labelledby={titleId} onClose={onClose} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="dialog-body">
        <h2 className="dialog-title" id={titleId}>{title}</h2>
        {children}
      </div>
    </dialog>
  );
}
