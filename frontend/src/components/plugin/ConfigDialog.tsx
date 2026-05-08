/**
 * 插件配置弹窗组件。
 *
 * 根据插件的 config_schema 自动渲染表单：
 * - level: "global" 的字段 → 全局配置区
 * - level: "account" 的字段 → 账号配置区
 * - 无 level → 默认 account
 *
 * 配置合并顺序（前端用于展示）：
 * schema defaults < globalConfig < accountConfig
 */
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { getErrMsg } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/misc";

export interface ConfigField {
  key: string;
  title?: string;
  type: string;
  default?: unknown;
  description?: string;
  minimum?: number;
  maximum?: number;
  level?: "global" | "account";
}

export interface ConfigSchema {
  type: string;
  properties: Record<string, ConfigField>;
  required?: string[];
}

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pluginKey: string;
  pluginName: string;
  schema: ConfigSchema | Record<string, unknown> | null;
  accountName?: string;
  accountId?: number;
  globalConfig?: Record<string, unknown>;
  accountConfig?: Record<string, unknown>;
  /** 保存回调，返回更新后的 effective config */
  onSave?: (globalVals: Record<string, unknown>, accountVals: Record<string, unknown>) => Promise<void>;
}

export function ConfigDialog({
  open, onOpenChange, pluginKey, pluginName, schema, accountName,
  accountId, globalConfig = {}, accountConfig = {}, onSave,
}: ConfigDialogProps) {
  const [globalVals, setGlobalVals] = useState<Record<string, unknown>>({});
  const [accountVals, setAccountVals] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);

  // 初始化配置值
  useEffect(() => {
    if (open && schema && typeof schema === "object" && "properties" in schema) {
      const s = schema as ConfigSchema;
      const gv: Record<string, unknown> = {};
      const av: Record<string, unknown> = {};
      for (const [k, f] of Object.entries(s.properties)) {
        // 合并顺序：schema defaults < globalConfig < accountConfig
        const effectiveVal = accountConfig[k] ?? globalConfig[k] ?? f.default;
        if (f.level === "global") {
          gv[k] = effectiveVal;
        } else {
          av[k] = effectiveVal;
        }
      }
      setGlobalVals(gv);
      setAccountVals(av);
    }
  }, [open, schema, globalConfig, accountConfig]);

  const s = schema as ConfigSchema | null;
  if (!s?.properties || Object.keys(s.properties).length === 0) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{pluginName} — 配置</DialogTitle>
            <DialogDescription>该插件没有可配置的选项。</DialogDescription>
          </DialogHeader>
          <DialogFooter><Button onClick={() => onOpenChange(false)}>关闭</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  const globalFields = Object.entries(s.properties).filter(([, f]) => f.level === "global");
  const accountFields = Object.entries(s.properties).filter(([, f]) => f.level !== "global");

  const handleSave = useCallback(async () => {
    if (!onSave) return;
    setSaving(true);
    try {
      await onSave(globalVals, accountVals);
      toast.success("配置已保存");
      onOpenChange(false);
    } catch (err) {
      toast.error(getErrMsg(err));
    } finally {
      setSaving(false);
    }
  }, [onSave, globalVals, accountVals, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{pluginName} — 配置</DialogTitle>
          <DialogDescription>
            插件: <code className="text-xs">{pluginKey}</code>
            {accountName && <> · 账号: {accountName}</>}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-5">
          {globalFields.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="text-sm font-medium">📦 全局配置</span>
                <span className="text-xs text-muted-foreground">所有账号共享</span>
              </div>
              <div className="space-y-3 rounded-lg border border-border p-4">
                {globalFields.map(([key, field]) => (
                  <FieldInput key={key} fk={key} field={field} value={globalVals[key]} onChange={(v) => setGlobalVals(p => ({...p, [key]: v}))} />
                ))}
              </div>
            </div>
          )}
          {accountFields.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="text-sm font-medium">👤 账号配置</span>
                <span className="text-xs text-muted-foreground">{accountName ? accountName + " 专属" : "按账号隔离"}</span>
              </div>
              <div className="space-y-3 rounded-lg border border-border p-4">
                {accountFields.map(([key, field]) => (
                  <FieldInput key={key} fk={key} field={field} value={accountVals[key]} onChange={(v) => setAccountVals(p => ({...p, [key]: v}))} />
                ))}
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? <><Spinner className="mr-2 h-4 w-4" /> 保存中…</> : "保存"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface FieldInputProps {
  fk: string;
  field: ConfigField;
  value: unknown;
  onChange: (v: unknown) => void;
}

function FieldInput({ fk, field, value, onChange }: FieldInputProps) {
  const label = field.title || fk;

  if (field.type === "boolean") {
    return (
      <label className="flex items-center gap-3 text-sm">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-input"
        />
        <div>
          <span className="font-medium">{label}</span>
          {field.description && <span className="ml-2 text-xs text-muted-foreground">{field.description}</span>}
        </div>
      </label>
    );
  }

  if (field.type === "integer" || field.type === "number") {
    return (
      <div>
        <label className="text-sm font-medium">{label}</label>
        {field.description && <p className="text-xs text-muted-foreground">{field.description}</p>}
        <input
          type="number"
          value={value != null ? String(value) : ""}
          min={field.minimum as number}
          max={field.maximum as number}
          onChange={(e) => {
            const v = e.target.value;
            onChange(v === "" ? null : Number(v));
          }}
          className="mt-1 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
        />
        {field.minimum !== undefined && field.maximum !== undefined && (
          <p className="mt-0.5 text-xs text-muted-foreground">范围: {field.minimum} — {field.maximum}</p>
        )}
      </div>
    );
  }

  // 默认：string 类型
  return (
    <div>
      <label className="text-sm font-medium">{label}</label>
      {field.description && <p className="text-xs text-muted-foreground">{field.description}</p>}
      <input
        type="text"
        value={value != null ? String(value) : ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.default != null ? String(field.default) : ""}
        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
      />
    </div>
  );
}
