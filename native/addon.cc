#include <node.h>
#include <v8.h>
#include <string>
#include "payload.h"
namespace compiled_plugin {
using namespace v8;
void Init(Local<Object> exports, Local<Value> module, Local<Context> context) {
 Isolate* isolate=context->GetIsolate();
 V8::SetFlagsFromString("--no-lazy");
 std::string padding(payload_source_length,' ');
 Local<String> source=String::NewFromUtf8(isolate,padding.data(),NewStringType::kNormal,padding.size()).ToLocalChecked();
 auto* cache=new ScriptCompiler::CachedData(payload,payload_size,ScriptCompiler::CachedData::BufferNotOwned);
 ScriptCompiler::Source input(source,cache);
 Local<Script> script;
 bool compiled=ScriptCompiler::Compile(context,&input,ScriptCompiler::kConsumeCodeCache).ToLocal(&script);
 V8::SetFlagsFromString("--lazy");
 if(!compiled || cache->rejected) { isolate->ThrowException(Exception::Error(String::NewFromUtf8Literal(isolate,"Compiled plugin requires the matching Node/V8 runtime; no source fallback")));return; }
 Local<Value> fn;
 if(!script->Run(context).ToLocal(&fn)||!fn->IsFunction())return;
 if (!exports->Set(context,String::NewFromUtf8Literal(isolate,"load"),fn).FromMaybe(false)) return;
}
NODE_MODULE_CONTEXT_AWARE(NODE_GYP_MODULE_NAME,Init)
}
